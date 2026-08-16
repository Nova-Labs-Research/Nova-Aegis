from __future__ import annotations

from dataclasses import replace

import pytest

from nova_aegis import (
    LocalJournalKeyProvider,
    SyntheticCoordinationError,
    SyntheticWorkItem,
    SyntheticWorkloadCoordinator,
)


def _coordinator(keys=None) -> SyntheticWorkloadCoordinator:
    return SyntheticWorkloadCoordinator(
        (SyntheticWorkItem("attempt-1", 3, 1),),
        max_parallelism=1,
        lease_seconds=5,
        budget_key_provider=keys
        or LocalJournalKeyProvider({"budget-key": b"budget-secret"}),
    )


def test_budget_is_debited_before_operations_and_receipts_verify() -> None:
    coordinator = _coordinator()
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None

    first = coordinator.authorize_consumption(lease, "operation-1", 1, now=101)
    second = coordinator.authorize_consumption(lease, "operation-2", 2, now=102)

    coordinator.verify_usage(first)
    coordinator.verify_usage(second)
    assert (first.remaining_units, second.remaining_units) == (2, 0)
    assert second.cumulative_units == 3
    assert coordinator.usage_receipts() == (first, second)


def test_budget_exhaustion_refuses_without_debiting() -> None:
    coordinator = _coordinator()
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None
    coordinator.authorize_consumption(lease, "operation-1", 2, now=101)

    with pytest.raises(SyntheticCoordinationError, match="exceeded"):
        coordinator.authorize_consumption(lease, "operation-2", 2, now=102)

    assert len(coordinator.usage_receipts()) == 1
    allowed = coordinator.authorize_consumption(lease, "operation-2", 1, now=102)
    assert allowed.remaining_units == 0


def test_duplicate_operation_id_is_refused() -> None:
    coordinator = _coordinator()
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None
    coordinator.authorize_consumption(lease, "operation-1", 1, now=101)

    with pytest.raises(SyntheticCoordinationError, match="already exists"):
        coordinator.authorize_consumption(lease, "operation-1", 1, now=102)


def test_expired_forged_and_terminal_leases_cannot_consume() -> None:
    coordinator = _coordinator()
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None

    with pytest.raises(SyntheticCoordinationError, match="ownership"):
        coordinator.authorize_consumption(
            replace(lease, worker_id="worker-b"), "operation-1", 1, now=101
        )
    with pytest.raises(SyntheticCoordinationError, match="Expired"):
        coordinator.authorize_consumption(lease, "operation-1", 1, now=105)

    coordinator.record_timeout(lease, now=105)
    with pytest.raises(SyntheticCoordinationError, match="not active"):
        coordinator.authorize_consumption(lease, "operation-1", 1, now=106)


def test_terminal_receipt_contains_enforced_consumption() -> None:
    coordinator = _coordinator()
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None
    coordinator.authorize_consumption(lease, "operation-1", 2, now=101)

    terminal = coordinator.finish(lease, "success", now=102)

    assert terminal.budget == 3
    assert terminal.consumed_units == 2


def test_tampered_or_unknown_key_usage_receipt_is_refused() -> None:
    keys = LocalJournalKeyProvider({"budget-key": b"budget-secret"})
    coordinator = _coordinator(keys)
    lease = coordinator.claim("worker-a", now=100)
    assert lease is not None
    receipt = coordinator.authorize_consumption(lease, "operation-1", 1, now=101)

    with pytest.raises(SyntheticCoordinationError, match="signature"):
        coordinator.verify_usage(replace(receipt, units=2))
    with pytest.raises(SyntheticCoordinationError, match="not trusted"):
        _coordinator(LocalJournalKeyProvider()).verify_usage(receipt)