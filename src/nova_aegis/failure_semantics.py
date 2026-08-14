"""Fail-closed crash and destructive-failure semantics for synthetic attempts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


class SyntheticFailureError(RuntimeError):
    """Raised when a synthetic failure lifecycle is violated."""


@dataclass(frozen=True)
class SyntheticFailureReceipt:
    attempt_id: str
    failure_kind: str
    detail: str
    timeout_seconds: float
    teardown_verified: bool


class SyntheticFailureLedger:
    """Append-only local failure ledger with explicit no-replay semantics."""

    FAILURE_KINDS: ClassVar[frozenset[str]] = frozenset(
        {"crash", "timeout", "corruption", "self_invalidated", "unavailable"}
    )

    def __init__(self, timeout_seconds: float) -> None:
        if timeout_seconds <= 0:
            raise ValueError("Synthetic failure timeout must be positive")
        self.timeout_seconds = timeout_seconds
        self._receipts: list[SyntheticFailureReceipt] = []
        self._attempts: set[str] = set()
        self._teardown_verified: set[str] = set()

    def begin(self, attempt_id: str) -> None:
        if not attempt_id.strip():
            raise ValueError("Synthetic attempt ID is required")
        if attempt_id in self._attempts:
            raise SyntheticFailureError("Synthetic attempt already exists")
        self._attempts.add(attempt_id)

    def record_failure(self, attempt_id: str, failure_kind: str, detail: str) -> SyntheticFailureReceipt:
        if attempt_id not in self._attempts:
            raise SyntheticFailureError("Synthetic attempt is unavailable")
        if any(receipt.attempt_id == attempt_id for receipt in self._receipts):
            raise SyntheticFailureError("Synthetic attempt already has a terminal failure")
        if failure_kind not in self.FAILURE_KINDS:
            raise ValueError("Synthetic failure kind is invalid")
        if not detail.strip():
            raise ValueError("Synthetic failure detail is required")
        receipt = SyntheticFailureReceipt(
            attempt_id,
            failure_kind,
            detail,
            self.timeout_seconds,
            attempt_id in self._teardown_verified,
        )
        self._receipts.append(receipt)
        return receipt

    def verify_teardown(self, attempt_id: str) -> None:
        if attempt_id not in self._attempts:
            raise SyntheticFailureError("Synthetic attempt is unavailable")
        self._teardown_verified.add(attempt_id)

    def receipts(self) -> tuple[SyntheticFailureReceipt, ...]:
        return tuple(self._receipts)

    def replay(self, attempt_id: str) -> SyntheticFailureReceipt:
        raise SyntheticFailureError("Synthetic failure receipts cannot be replayed")
