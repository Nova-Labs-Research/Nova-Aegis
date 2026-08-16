"""Bounded deterministic coordination for synthetic local workload attempts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Iterable


class SyntheticCoordinationError(RuntimeError):
    """Raised when synthetic workload ownership or lifecycle is invalid."""


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
    seed: int
    terminal_at: int


class SyntheticWorkloadCoordinator:
    """Process-local one-attempt coordinator with no retry or replay path."""

    OUTCOMES: ClassVar[frozenset[str]] = frozenset({"success", "failure", "crash"})

    def __init__(
        self,
        items: Iterable[SyntheticWorkItem],
        *,
        max_parallelism: int,
        lease_seconds: int,
    ) -> None:
        if max_parallelism <= 0 or lease_seconds <= 0:
            raise ValueError("Synthetic coordination bounds must be positive")
        ordered = tuple(sorted(items, key=lambda item: (item.seed, item.attempt_id)))
        if len({item.attempt_id for item in ordered}) != len(ordered):
            raise ValueError("Synthetic work item IDs must be unique")
        self.max_parallelism = max_parallelism
        self.lease_seconds = lease_seconds
        self._items = {item.attempt_id: item for item in ordered}
        self._pending = [item.attempt_id for item in ordered]
        self._active: dict[str, SyntheticWorkLease] = {}
        self._receipts: list[SyntheticWorkReceipt] = []
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
            item.seed,
            terminal_at,
        )
        del self._active[item.attempt_id]
        self._receipts.append(receipt)
        return receipt