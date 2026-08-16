"""Bounded deterministic coordination for synthetic local workload attempts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Any, ClassVar, Iterable, Mapping, Protocol


class SyntheticCoordinationError(RuntimeError):
    """Raised when synthetic workload ownership or lifecycle is invalid."""


class SyntheticBudgetKeyProvider(Protocol):
    def get(self, key_id: str) -> bytes | None: ...

    def active(self) -> tuple[str, bytes] | None: ...


@dataclass(frozen=True)
class SyntheticWorkItem:
    attempt_id: str
    budget: int
    seed: int

    def __post_init__(self) -> None:
        if not self.attempt_id.strip() or self.budget <= 0:
            raise ValueError("Synthetic work item fields are invalid")


@dataclass(frozen=True)
class SyntheticWorkLease:
    attempt_id: str
    worker_id: str
    fencing_token: int
    lease_expires_at: int


@dataclass(frozen=True)
class SyntheticWorkReceipt:
    attempt_id: str
    worker_id: str
    fencing_token: int
    outcome: str
    budget: int
    consumed_units: int
    seed: int
    terminal_at: int


@dataclass(frozen=True)
class SyntheticBudgetUsageReceipt:
    attempt_id: str
    operation_id: str
    worker_id: str
    fencing_token: int
    units: int
    cumulative_units: int
    remaining_units: int
    authorized_at: int
    key_id: str
    signature: str

    def payload(self) -> dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "operation_id": self.operation_id,
            "worker_id": self.worker_id,
            "fencing_token": self.fencing_token,
            "units": self.units,
            "cumulative_units": self.cumulative_units,
            "remaining_units": self.remaining_units,
            "authorized_at": self.authorized_at,
            "key_id": self.key_id,
        }


class SyntheticWorkloadCoordinator:
    """Process-local one-attempt coordinator with no retry or replay path."""

    OUTCOMES: ClassVar[frozenset[str]] = frozenset({"success", "failure", "crash"})

    def __init__(
        self,
        items: Iterable[SyntheticWorkItem],
        *,
        max_parallelism: int,
        lease_seconds: int,
        budget_key_provider: SyntheticBudgetKeyProvider,
    ) -> None:
        if max_parallelism <= 0 or lease_seconds <= 0:
            raise ValueError("Synthetic coordination bounds must be positive")
        ordered = tuple(sorted(items, key=lambda item: (item.seed, item.attempt_id)))
        if len({item.attempt_id for item in ordered}) != len(ordered):
            raise ValueError("Synthetic work item IDs must be unique")
        self.max_parallelism = max_parallelism
        self.lease_seconds = lease_seconds
        self._budget_key_provider = budget_key_provider
        self._items = {item.attempt_id: item for item in ordered}
        self._pending = [item.attempt_id for item in ordered]
        self._active: dict[str, SyntheticWorkLease] = {}
        self._receipts: list[SyntheticWorkReceipt] = []
        self._usage_receipts: list[SyntheticBudgetUsageReceipt] = []
        self._consumed_units = {item.attempt_id: 0 for item in ordered}
        self._operation_ids: set[tuple[str, str]] = set()
        self._next_fencing_token = 1

    def claim(self, worker_id: str, *, now: int) -> SyntheticWorkLease | None:
        if not worker_id.strip():
            raise ValueError("Synthetic worker identity is required")
        if len(self._active) >= self.max_parallelism or not self._pending:
            return None
        attempt_id = self._pending.pop(0)
        lease = SyntheticWorkLease(
            attempt_id,
            worker_id,
            self._next_fencing_token,
            now + self.lease_seconds,
        )
        self._next_fencing_token += 1
        self._active[attempt_id] = lease
        return lease

    def authorize_consumption(
        self,
        lease: SyntheticWorkLease,
        operation_id: str,
        units: int,
        *,
        now: int,
    ) -> SyntheticBudgetUsageReceipt:
        if not operation_id.strip() or units <= 0:
            raise ValueError("Synthetic budget operation and units are invalid")
        active = self._require_active_lease(lease)
        if now >= active.lease_expires_at:
            raise SyntheticCoordinationError("Expired synthetic lease cannot consume budget")
        operation_key = (lease.attempt_id, operation_id)
        if operation_key in self._operation_ids:
            raise SyntheticCoordinationError("Synthetic budget operation already exists")
        item = self._items[lease.attempt_id]
        cumulative_units = self._consumed_units[lease.attempt_id] + units
        if cumulative_units > item.budget:
            raise SyntheticCoordinationError("Synthetic work budget would be exceeded")
        active_key = self._budget_key_provider.active()
        if active_key is None:
            raise SyntheticCoordinationError("Synthetic budget requires an active signing key")
        key_id, secret = active_key
        unsigned = SyntheticBudgetUsageReceipt(
            lease.attempt_id,
            operation_id,
            lease.worker_id,
            lease.fencing_token,
            units,
            cumulative_units,
            item.budget - cumulative_units,
            now,
            key_id,
            "",
        )
        receipt = SyntheticBudgetUsageReceipt(
            **unsigned.payload(),
            signature=hmac.new(secret, _canonical(unsigned.payload()), hashlib.sha256).hexdigest(),
        )
        self._consumed_units[lease.attempt_id] = cumulative_units
        self._operation_ids.add(operation_key)
        self._usage_receipts.append(receipt)
        return receipt

    def verify_usage(self, receipt: SyntheticBudgetUsageReceipt) -> None:
        secret = self._budget_key_provider.get(receipt.key_id)
        if secret is None:
            raise SyntheticCoordinationError("Synthetic budget signing key is not trusted")
        expected = hmac.new(secret, _canonical(receipt.payload()), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(receipt.signature, expected):
            raise SyntheticCoordinationError("Synthetic budget receipt signature is invalid")

    def usage_receipts(self) -> tuple[SyntheticBudgetUsageReceipt, ...]:
        return tuple(self._usage_receipts)

    def finish(
        self,
        lease: SyntheticWorkLease,
        outcome: str,
        *,
        now: int,
    ) -> SyntheticWorkReceipt:
        if outcome not in self.OUTCOMES:
            raise ValueError("Synthetic work outcome is invalid")
        active = self._require_active_lease(lease)
        if now >= active.lease_expires_at:
            raise SyntheticCoordinationError("Expired synthetic lease requires explicit timeout recording")
        return self._record(active, outcome, now)

    def record_timeout(
        self,
        lease: SyntheticWorkLease,
        *,
        now: int,
    ) -> SyntheticWorkReceipt:
        active = self._require_active_lease(lease)
        if now < active.lease_expires_at:
            raise SyntheticCoordinationError("Synthetic lease has not expired")
        return self._record(active, "timeout", now)

    def receipts(self) -> tuple[SyntheticWorkReceipt, ...]:
        return tuple(self._receipts)

    def replay(self, attempt_id: str) -> SyntheticWorkLease:
        raise SyntheticCoordinationError("Synthetic work attempts cannot be replayed")

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def active_count(self) -> int:
        return len(self._active)

    def _require_active_lease(self, lease: SyntheticWorkLease) -> SyntheticWorkLease:
        active = self._active.get(lease.attempt_id)
        if active is None:
            raise SyntheticCoordinationError("Synthetic work attempt is not active")
        if active != lease:
            raise SyntheticCoordinationError("Synthetic work lease ownership is invalid")
        return active

    def _record(
        self,
        lease: SyntheticWorkLease,
        outcome: str,
        terminal_at: int,
    ) -> SyntheticWorkReceipt:
        item = self._items[lease.attempt_id]
        receipt = SyntheticWorkReceipt(
            item.attempt_id,
            lease.worker_id,
            lease.fencing_token,
            outcome,
            item.budget,
            self._consumed_units[item.attempt_id],
            item.seed,
            terminal_at,
        )
        del self._active[item.attempt_id]
        self._receipts.append(receipt)
        return receipt


def _canonical(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")