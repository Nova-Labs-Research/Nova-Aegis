from __future__ import annotations

import pytest

from nova_aegis import SyntheticFailureError, SyntheticFailureLedger


@pytest.mark.parametrize("failure_kind", ["crash", "timeout", "corruption", "self_invalidated", "unavailable"])
def test_failure_kinds_create_terminal_receipts(failure_kind: str) -> None:
    ledger = SyntheticFailureLedger(0.25)
    ledger.begin("attempt-1")
    ledger.verify_teardown("attempt-1")

    receipt = ledger.record_failure("attempt-1", failure_kind, "synthetic failure")

    assert receipt.failure_kind == failure_kind
    assert receipt.timeout_seconds == 0.25
    assert receipt.teardown_verified is True
    assert ledger.receipts() == (receipt,)


def test_failure_receipt_cannot_be_replayed_or_recorded_twice() -> None:
    ledger = SyntheticFailureLedger(1.0)
    ledger.begin("attempt-1")
    ledger.record_failure("attempt-1", "crash", "subject crashed")

    with pytest.raises(SyntheticFailureError, match="replayed"):
        ledger.replay("attempt-1")
    with pytest.raises(SyntheticFailureError, match="terminal"):
        ledger.record_failure("attempt-1", "timeout", "late timeout")


def test_unknown_attempt_invalid_kind_and_invalid_timeout_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive"):
        SyntheticFailureLedger(0)

    ledger = SyntheticFailureLedger(1.0)
    with pytest.raises(SyntheticFailureError, match="unavailable"):
        ledger.record_failure("missing", "crash", "detail")
    ledger.begin("attempt-1")
    with pytest.raises(ValueError, match="invalid"):
        ledger.record_failure("attempt-1", "repair", "detail")


def test_failure_ledger_is_append_only_to_callers() -> None:
    ledger = SyntheticFailureLedger(1.0)
    ledger.begin("attempt-1")
    receipt = ledger.record_failure("attempt-1", "corruption", "invalid state")

    receipts = ledger.receipts()
    assert receipts == (receipt,)
    with pytest.raises(AttributeError):
        receipts.append(receipt)  # type: ignore[attr-defined]
