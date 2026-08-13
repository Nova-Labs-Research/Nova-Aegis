"""Synthetic MCP Gateway boundary with explicit local authorization contracts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import secrets
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
    ) -> None:
        if not resource_uri.startswith("https://"):
            raise ValueError("MCP resource URI must use HTTPS")
        if lifetime_seconds < 1:
            raise ValueError("MCP token lifetime must be positive")
        self.resource_uri = resource_uri.rstrip("/")
        self._identity_authority = identity_authority
        self._praetor = praetor
        self._audit_log = audit_log
        self._tools = dict(tools)
        self._secret = secret or secrets.token_bytes(32)
        self._lifetime_seconds = lifetime_seconds
        self._issued_tokens: dict[str, IdentityCredential] = {}

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
        return McpTaskState(
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
            return self._invoke_authorized(access_token, request.name, request.parameters, context)
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
        if task_state.expires_at <= int(time.time()):
            raise McpGatewayError("MCP task state is expired")
        if (
            task_state.user_id,
            task_state.role,
            task_state.audience,
            task_state.tool_name,
            task_state.parameters_hash,
        ) != (
            context.user_id,
            context.role,
            self.resource_uri,
            request.name,
            self._parameters_hash(request.parameters),
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
