from __future__ import annotations

from dataclasses import replace

import pytest

from nova_aegis import (
    LocalJournalKeyProvider,
    SyntheticCoordinationError,
    SyntheticWorkItem,
    SyntheticWorkloadCoordinator,
)


def _coordinator(*, max_parallelism: int = 2) -> SyntheticWorkloadCoordinator:
    return SyntheticWorkloadCoordinator(
        (
            SyntheticWorkItem("attempt-c", 3, 30),
            SyntheticWorkItem("attempt-a", 1, 10),
            SyntheticWorkItem("attempt-b", 2, 20),
        ),
        max_parallelism=max_parallelism,
        lease_seconds=5,
        budget_key_provider=LocalJournalKeyProvider({"budget-key": b"budget-secret"}),
    )


def test_claims_are_deterministic_and_parallelism_is_bounded() -> None:
    coordinator = _coordinator()

    first = coordinator.claim("worker-a", now=100)
    second = coordinator.claim("worker-b", now=100)

    assert first is not None and first.attempt_id == "attempt-a"
    assert second is not None and second.attempt_id == "attempt-b"
    assert coordinator.claim("worker-c", now=100) is None
    assert coordinator.active_count == 2
    assert coordinator.pending_count == 1


def test_completion_creates_one_terminal_receipt_and_cannot_replay() -> None:
    coordinator = _coordinator(max_parallelism=1)
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None

    receipt = coordinator.finish(lease, "success", now=101)

    assert receipt.attempt_id == lease.attempt_id
    assert receipt.budget == 1
    assert coordinator.receipts() == (receipt,)
    with pytest.raises(SyntheticCoordinationError, match="not active"):
        coordinator.finish(lease, "success", now=102)
    with pytest.raises(SyntheticCoordinationError, match="replayed"):
        coordinator.replay(lease.attempt_id)


def test_crash_and_timeout_are_distinct_terminal_outcomes_without_requeue() -> None:
    coordinator = _coordinator()
    crashed = coordinator.claim("worker-a", now=100)
    timed_out = coordinator.claim("worker-b", now=100)
    assert crashed is not None and timed_out is not None

    crash_receipt = coordinator.finish(crashed, "crash", now=101)
    timeout_receipt = coordinator.record_timeout(timed_out, now=105)

    assert (crash_receipt.outcome, timeout_receipt.outcome) == ("crash", "timeout")
    assert coordinator.pending_count == 1
    assert coordinator.active_count == 0
    assert coordinator.claim("worker-c", now=106).attempt_id == "attempt-c"  # type: ignore[union-attr]
    assert coordinator.claim("worker-d", now=106) is None


def test_stale_or_forged_lease_ownership_is_refused() -> None:
    coordinator = _coordinator(max_parallelism=1)
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None

    with pytest.raises(SyntheticCoordinationError, match="ownership"):
        coordinator.finish(replace(lease, worker_id="worker-b"), "success", now=101)
    with pytest.raises(SyntheticCoordinationError, match="ownership"):
        coordinator.finish(replace(lease, fencing_token=999), "success", now=101)


def test_expired_lease_requires_explicit_timeout_receipt() -> None:
    coordinator = _coordinator(max_parallelism=1)
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None

    with pytest.raises(SyntheticCoordinationError, match="explicit timeout"):
        coordinator.finish(lease, "failure", now=105)
    with pytest.raises(SyntheticCoordinationError, match="not expired"):
        coordinator.record_timeout(lease, now=104)
    assert coordinator.record_timeout(lease, now=105).outcome == "timeout"


def test_invalid_bounds_duplicate_attempts_and_outcomes_fail_closed() -> None:
    item = SyntheticWorkItem("attempt-a", 1, 1)
    with pytest.raises(ValueError, match="positive"):
        SyntheticWorkloadCoordinator(
            (item,),
            max_parallelism=0,
            lease_seconds=1,
            budget_key_provider=LocalJournalKeyProvider(),
        )
    with pytest.raises(ValueError, match="unique"):
        SyntheticWorkloadCoordinator(
            (item, item),
            max_parallelism=1,
            lease_seconds=1,
            budget_key_provider=LocalJournalKeyProvider(),
        )

    coordinator = SyntheticWorkloadCoordinator(
        (item,),
        max_parallelism=1,
        lease_seconds=1,
        budget_key_provider=LocalJournalKeyProvider({"budget-key": b"budget-secret"}),
    )
    lease = coordinator.claim("worker-a", now=0)
    assert lease is not None
    with pytest.raises(ValueError, match="outcome"):
        coordinator.finish(lease, "retry", now=0)