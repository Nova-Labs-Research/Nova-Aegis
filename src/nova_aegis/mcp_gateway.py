"""Synthetic MCP Gateway boundary with explicit local authorization contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import secrets
import threading
import time
from typing import Any, Callable, Mapping

from .core import (
    AssuranceStatus,
    AuditLog,
    AuthorizationContext,
    IdentityAuthority,
    IdentityCredential,
    IdentityError,
    Praetor,
)


class McpGatewayError(RuntimeError):
    """Raised when a synthetic MCP request violates the gateway contract."""


@dataclass(frozen=True)
class McpAccessToken:
    token: str
    user_id: str
    role: str
    audience: str
    scopes: frozenset[str]
    issued_at: int
    expires_at: int
    signature: str


@dataclass(frozen=True)
class McpToolDescriptor:
    name: str
    required_scope: str
    allowed_parameters: frozenset[str]
    handler: Callable[[Mapping[str, str]], dict[str, str]]


@dataclass(frozen=True)
class McpTaskState:
    task_id: str
    user_id: str
    role: str
    audience: str
    tool_name: str
    parameters_hash: str
    issued_at: int
    expires_at: int
    signature: str


@dataclass(frozen=True)
class McpGatewayRequest:
    method: str
    name: str
    parameters: Mapping[str, str]
    task_state: McpTaskState
    meta: Mapping[str, Any] | None = None


@dataclass
class _TaskRecord:
    user_id: str
    expires_at: int
    status: str


class McpGateway:
    """A synthetic server-side MCP boundary; it is not an OAuth or HTTP implementation."""

    def __init__(
        self,
        *,
        resource_uri: str,
        identity_authority: IdentityAuthority,
        praetor: Praetor,
        audit_log: AuditLog,
        tools: Mapping[str, McpToolDescriptor],
        secret: bytes | None = None,
        lifetime_seconds: int = 300,
        max_active_tasks_per_user: int = 2,
    ) -> None:
        if not resource_uri.startswith("https://"):
            raise ValueError("MCP resource URI must use HTTPS")
        if lifetime_seconds < 1:
            raise ValueError("MCP token lifetime must be positive")
        if max_active_tasks_per_user < 1:
            raise ValueError("MCP active task quota must be positive")
        self.resource_uri = resource_uri.rstrip("/")
        self._identity_authority = identity_authority
        self._praetor = praetor
        self._audit_log = audit_log
        self._tools = dict(tools)
        self._secret = secret or secrets.token_bytes(32)
        self._lifetime_seconds = lifetime_seconds
        self._max_active_tasks_per_user = max_active_tasks_per_user
        self._issued_tokens: dict[str, IdentityCredential] = {}
        self._task_lock = threading.Lock()
        self._completed_tasks: dict[str, dict[str, str]] = {}
        self._inflight_tasks: set[str] = set()
        self._tasks: dict[str, _TaskRecord] = {}

    def create_task_state(
        self,
        *,
        access_token: McpAccessToken,
        tool_name: str,
        parameters: Mapping[str, str],
    ) -> McpTaskState:
        context = self._validate_token(access_token)
        if tool_name not in self._tools:
            raise McpGatewayError("MCP tool is not registered")
        with self._task_lock:
            self._expire_tasks()
            active_count = sum(
                record.user_id == context.user_id and record.status in {"pending", "in_progress"}
                for record in self._tasks.values()
            )
            if active_count >= self._max_active_tasks_per_user:
                raise McpGatewayError("MCP active task quota is exhausted")
        parameters_hash = self._parameters_hash(parameters)
        issued_at = int(time.time())
        expires_at = issued_at + self._lifetime_seconds
        task_id = secrets.token_urlsafe(24)
        signature = self._sign_task(
            task_id,
            context,
            self.resource_uri,
            tool_name,
            parameters_hash,
            issued_at,
            expires_at,
        )
        state = McpTaskState(
            task_id,
            context.user_id,
            context.role,
            self.resource_uri,
            tool_name,
            parameters_hash,
            issued_at,
            expires_at,
            signature,
        )
        with self._task_lock:
            self._tasks[task_id] = _TaskRecord(context.user_id, expires_at, "pending")
        self._audit_log.append(
            "mcp_task_created",
            task_id=task_id,
            tool=tool_name,
            user_id=context.user_id,
        )
        return state

    def cancel_task(
        self,
        *,
        access_token: McpAccessToken,
        task_state: McpTaskState,
    ) -> None:
        context = self._validate_token(access_token)
        self._validate_task_identity(task_state, context)
        with self._task_lock:
            self._expire_tasks()
            record = self._tasks.get(task_state.task_id)
            if record is None or record.status != "pending":
                raise McpGatewayError("MCP task cannot be cancelled in its current state")
            record.status = "cancelled"
        self._audit_log.append(
            "mcp_task_cancelled",
            task_id=task_state.task_id,
            tool=task_state.tool_name,
            user_id=context.user_id,
        )

    def task_status(self, task_state: McpTaskState) -> str:
        with self._task_lock:
            self._expire_tasks()
            record = self._tasks.get(task_state.task_id)
            return record.status if record is not None else "unknown"

    def discover_tools(self, credential: IdentityCredential) -> tuple[McpToolDescriptor, ...]:
        context = self._identity_authority.authenticate(credential)
        return tuple(
            descriptor
            for descriptor in self._tools.values()
            if self._is_role_eligible(descriptor, context)
        )

    def issue_token(
        self,
        credential: IdentityCredential,
        *,
        audience: str,
        scopes: frozenset[str],
    ) -> McpAccessToken:
        context = self._identity_authority.authenticate(credential)
        if audience.rstrip("/") != self.resource_uri:
            raise McpGatewayError("MCP token audience does not match this gateway")
        if not scopes or any(scope not in self._known_scopes for scope in scopes):
            raise McpGatewayError("MCP token contains an unknown or empty scope set")
        issued_at = int(time.time())
        expires_at = issued_at + self._lifetime_seconds
        token = secrets.token_urlsafe(24)
        signature = self._sign(token, context, audience, scopes, issued_at, expires_at)
        self._issued_tokens[token] = credential
        return McpAccessToken(
            token,
            context.user_id,
            context.role,
            self.resource_uri,
            scopes,
            issued_at,
            expires_at,
            signature,
        )

    def invoke(
        self,
        *,
        access_token: McpAccessToken,
        tool_name: str,
        parameters: Mapping[str, str],
    ) -> dict[str, Any]:
        try:
            context = self._validate_token(access_token)
            return self._invoke_authorized(access_token, tool_name, parameters, context)
        except (IdentityError, McpGatewayError, ValueError) as error:
            return self._blocked(tool_name, str(error))

    def invoke_stateless(
        self,
        *,
        access_token: McpAccessToken,
        headers: Mapping[str, str],
        request: McpGatewayRequest,
    ) -> dict[str, Any]:
        try:
            context = self._validate_token(access_token)
            self._validate_request_headers(headers, request)
            self._validate_task_state(request.task_state, context, request)
            self._validate_meta(request.meta)
            return self._invoke_stateless_once(access_token, request, context)
        except (IdentityError, McpGatewayError, ValueError) as error:
            return self._blocked(request.name, str(error))

    def _invoke_authorized(
        self,
        access_token: McpAccessToken,
        tool_name: str,
        parameters: Mapping[str, str],
        context: AuthorizationContext,
    ) -> dict[str, Any]:
        descriptor = self._tools.get(tool_name)
        if descriptor is None:
            raise McpGatewayError("MCP tool is not registered")
        if descriptor.required_scope not in access_token.scopes:
            raise McpGatewayError("MCP token lacks the required tool scope")
        self._validate_parameters(descriptor, parameters)
        decision = self._praetor.authorize_tool(
            tool_name,
            frozenset({tool_name}),
            context=context,
            parameters=parameters,
        )
        if decision.status is not AssuranceStatus.PASS:
            raise McpGatewayError(decision.reason)

        result = descriptor.handler(parameters)
        self._audit_log.append(
            "mcp_tool_executed",
            tool=tool_name,
            user_id=context.user_id,
            role=context.role,
            audience=access_token.audience,
            scopes=sorted(access_token.scopes),
        )
        return {"result": result, "assurance": AssuranceStatus.PASS.value, "warning": None}

    def _invoke_stateless_once(
        self,
        access_token: McpAccessToken,
        request: McpGatewayRequest,
        context: AuthorizationContext,
    ) -> dict[str, Any]:
        task_id = request.task_state.task_id
        with self._task_lock:
            completed = self._completed_tasks.get(task_id)
            if completed is not None:
                self._audit_log.append(
                    "mcp_task_replay_returned",
                    task_id=task_id,
                    tool=request.name,
                    user_id=context.user_id,
                )
                return {
                    "result": dict(completed),
                    "assurance": AssuranceStatus.PASS.value,
                    "warning": "MCP task already completed; returning the stored result",
                }
            if task_id in self._inflight_tasks:
                raise McpGatewayError("MCP task is already in progress")
            record = self._tasks.get(task_id)
            if record is None or record.status == "cancelled":
                raise McpGatewayError("MCP task is not active")
            if record.status != "pending":
                raise McpGatewayError("MCP task is not available for execution")
            record.status = "in_progress"
            self._inflight_tasks.add(task_id)
        try:
            response = self._invoke_authorized(
                access_token,
                request.name,
                request.parameters,
                context,
            )
            if response["assurance"] == AssuranceStatus.PASS.value:
                with self._task_lock:
                    self._completed_tasks[task_id] = dict(response["result"])
                    self._tasks[task_id].status = "completed"
            return response
        finally:
            with self._task_lock:
                self._inflight_tasks.discard(task_id)
                record = self._tasks.get(task_id)
                if record is not None and record.status == "in_progress":
                    record.status = "pending"

    def _blocked(self, tool_name: str, reason: str) -> dict[str, Any]:
        self._audit_log.append("mcp_request_blocked", tool=tool_name, reason=reason)
        return {"result": None, "assurance": AssuranceStatus.FAIL.value, "warning": reason}

    @property
    def _known_scopes(self) -> frozenset[str]:
        return frozenset(descriptor.required_scope for descriptor in self._tools.values())

    def _validate_token(self, token: McpAccessToken) -> AuthorizationContext:
        if not isinstance(token, McpAccessToken):
            raise McpGatewayError("MCP access token is invalid")
        credential = self._issued_tokens.get(token.token)
        if credential is None:
            raise McpGatewayError("MCP access token was not issued by this gateway")
        try:
            current_context = self._identity_authority.authenticate(credential)
        except IdentityError as error:
            raise McpGatewayError(f"MCP access token identity is invalid: {error}") from error
        if token.audience != self.resource_uri:
            raise McpGatewayError("MCP access token audience is invalid")
        if token.expires_at <= int(time.time()):
            raise McpGatewayError("MCP access token is expired")
        expected = self._sign(
            token.token,
            AuthorizationContext(token.user_id, token.role),
            token.audience,
            token.scopes,
            token.issued_at,
            token.expires_at,
        )
        if not secrets.compare_digest(token.signature, expected):
            raise McpGatewayError("MCP access token signature is invalid")
        if (token.user_id, token.role) != (current_context.user_id, current_context.role):
            raise McpGatewayError("MCP access token identity claims are invalid")
        return current_context

    @staticmethod
    def _validate_parameters(
        descriptor: McpToolDescriptor,
        parameters: Mapping[str, str],
    ) -> None:
        if set(parameters) != descriptor.allowed_parameters:
            raise McpGatewayError("MCP request parameters do not match the registered tool schema")
        if any(not isinstance(value, str) or not value.strip() for value in parameters.values()):
            raise McpGatewayError("MCP request parameters must be non-empty strings")

    def _validate_request_headers(
        self,
        headers: Mapping[str, str],
        request: McpGatewayRequest,
    ) -> None:
        if request.method != "tools/call" or request.name not in self._tools:
            raise McpGatewayError("MCP request method or name is invalid")
        if headers.get("Mcp-Method") != request.method or headers.get("Mcp-Name") != request.name:
            raise McpGatewayError("MCP header and request body routing fields do not match")

    def _validate_task_state(
        self,
        task_state: McpTaskState,
        context: AuthorizationContext,
        request: McpGatewayRequest,
    ) -> None:
        if not isinstance(task_state, McpTaskState):
            raise McpGatewayError("MCP task state is invalid")
        self._validate_task_identity(task_state, context)
        if task_state.tool_name != request.name or task_state.parameters_hash != self._parameters_hash(request.parameters):
            raise McpGatewayError("MCP task state does not match the request identity or operation")

    def _validate_task_identity(
        self,
        task_state: McpTaskState,
        context: AuthorizationContext,
    ) -> None:
        if not isinstance(task_state, McpTaskState):
            raise McpGatewayError("MCP task state is invalid")
        if task_state.expires_at <= int(time.time()):
            raise McpGatewayError("MCP task state is expired")
        if (
            task_state.user_id,
            task_state.role,
            task_state.audience,
        ) != (
            context.user_id,
            context.role,
            self.resource_uri,
        ):
            raise McpGatewayError("MCP task state does not match the request identity or operation")
        expected = self._sign_task(
            task_state.task_id,
            context,
            task_state.audience,
            task_state.tool_name,
            task_state.parameters_hash,
            task_state.issued_at,
            task_state.expires_at,
        )
        if not secrets.compare_digest(task_state.signature, expected):
            raise McpGatewayError("MCP task state signature is invalid")

    def _expire_tasks(self) -> None:
        now = int(time.time())
        for record in self._tasks.values():
            if record.status in {"pending", "in_progress"} and record.expires_at <= now:
                record.status = "expired"

    @staticmethod
    def _validate_meta(meta: Mapping[str, Any] | None) -> None:
        if meta is None:
            return
        if not isinstance(meta, Mapping):
            raise McpGatewayError("MCP _meta must be an object")
        forbidden = {"user_id", "role", "audience", "scope", "scopes", "authorization"}
        if forbidden.intersection(meta):
            raise McpGatewayError("MCP _meta cannot supply identity or authorization fields")

    @staticmethod
    def _parameters_hash(parameters: Mapping[str, str]) -> str:
        return hashlib.sha256(
            json.dumps(dict(parameters), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def _is_role_eligible(
        self,
        descriptor: McpToolDescriptor,
        context: AuthorizationContext,
    ) -> bool:
        policy = self._praetor.tool_policies.get(descriptor.name)
        return policy is not None and context.role in policy.allowed_roles

    def _sign(
        self,
        token: str,
        context: AuthorizationContext,
        audience: str,
        scopes: frozenset[str],
        issued_at: int,
        expires_at: int,
    ) -> str:
        payload = (
            f"{token}|{context.user_id}|{context.role}|{audience.rstrip('/')}|"
            f"{','.join(sorted(scopes))}|{issued_at}|{expires_at}"
        ).encode("utf-8")
        return hashlib.blake2b(payload, key=self._secret, digest_size=32).hexdigest()

    def _sign_task(
        self,
        task_id: str,
        context: AuthorizationContext,
        audience: str,
        tool_name: str,
        parameters_hash: str,
        issued_at: int,
        expires_at: int,
    ) -> str:
        payload = (
            f"{task_id}|{context.user_id}|{context.role}|{audience}|{tool_name}|"
            f"{parameters_hash}|{issued_at}|{expires_at}"
        ).encode("utf-8")
        return hashlib.blake2b(payload, key=self._secret, digest_size=32).hexdigest()
