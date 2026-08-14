"""Verifiable synthetic external execution receipts for MCP task recovery."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import secrets
import time
from typing import Mapping, Protocol


class ExternalReceiptError(RuntimeError):
    """Raised when an external execution receipt cannot be verified."""


@dataclass(frozen=True)
class ExternalExecutionReceipt:
    receipt_id: str
    task_id: str
    tool_name: str
    user_id: str
    audience: str
    status: str
    parameters_hash: str
    result_hash: str
    issued_at: int
    expires_at: int
    signature: str


class ExternalReceiptVerifier(Protocol):
    def verify(
        self,
        receipt_id: str,
        *,
        task_id: str,
        tool_name: str,
        user_id: str,
        audience: str,
        parameters_hash: str,
        result: Mapping[str, str],
    ) -> ExternalExecutionReceipt: ...


class LocalExternalReceiptRegistry:
    """Signed local receipt registry used to prove the verification boundary."""

    def __init__(self, *, secret: bytes | None = None, lifetime_seconds: int = 300) -> None:
        if lifetime_seconds < 1:
            raise ValueError("External receipt lifetime must be positive")
        self._secret = secret or secrets.token_bytes(32)
        self._lifetime_seconds = lifetime_seconds
        self._receipts: dict[str, ExternalExecutionReceipt] = {}

    def create(
        self,
        *,
        task_id: str,
        tool_name: str,
        user_id: str,
        audience: str,
        status: str,
        parameters_hash: str,
        result: Mapping[str, str],
    ) -> ExternalExecutionReceipt:
        if status not in {"completed", "abandoned"}:
            raise ValueError("External execution receipt status is invalid")
        receipt_id = secrets.token_urlsafe(24)
        issued_at = int(time.time())
        expires_at = issued_at + self._lifetime_seconds
        result_hash = hash_result(result)
        signature = self._sign(
            receipt_id,
            task_id,
            tool_name,
            user_id,
            audience,
            status,
            parameters_hash,
            result_hash,
            issued_at,
            expires_at,
        )
        receipt = ExternalExecutionReceipt(
            receipt_id,
            task_id,
            tool_name,
            user_id,
            audience,
            status,
            parameters_hash,
            result_hash,
            issued_at,
            expires_at,
            signature,
        )
        self._receipts[receipt_id] = receipt
        return receipt

    def verify(
        self,
        receipt_id: str,
        *,
        task_id: str,
        tool_name: str,
        user_id: str,
        audience: str,
        parameters_hash: str,
        result: Mapping[str, str],
    ) -> ExternalExecutionReceipt:
        receipt = self._receipts.get(receipt_id)
        if receipt is None:
            raise ExternalReceiptError("External execution receipt is not registered")
        if receipt.expires_at <= int(time.time()):
            raise ExternalReceiptError("External execution receipt is expired")
        expected_signature = self._sign(
            receipt.receipt_id,
            receipt.task_id,
            receipt.tool_name,
            receipt.user_id,
            receipt.audience,
            receipt.status,
            receipt.parameters_hash,
            receipt.result_hash,
            receipt.issued_at,
            receipt.expires_at,
        )
        if not secrets.compare_digest(receipt.signature, expected_signature):
            raise ExternalReceiptError("External execution receipt signature is invalid")
        if (task_id, tool_name, user_id, audience) != (
            receipt.task_id,
            receipt.tool_name,
            receipt.user_id,
            receipt.audience,
        ):
            raise ExternalReceiptError("External execution receipt does not match this task")
        if parameters_hash != receipt.parameters_hash:
            raise ExternalReceiptError("External execution receipt parameters do not match")
        if hash_result(result) != receipt.result_hash:
            raise ExternalReceiptError("External execution receipt result does not match")
        return receipt

    def _sign(self, *parts: object) -> str:
        payload = "|".join(str(part) for part in parts).encode("utf-8")
        return hashlib.blake2b(payload, key=self._secret, digest_size=32).hexdigest()


def hash_result(result: Mapping[str, str]) -> str:
    return hashlib.sha256(
        "|".join(
            f"{key}={result[key]}" for key in sorted(result)
        ).encode("utf-8")
    ).hexdigest()
