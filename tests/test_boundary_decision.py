from __future__ import annotations

from dataclasses import replace

import pytest

from nova_aegis import (
    BoundaryDecisionError,
    BoundaryPreflightReport,
    SignedBoundaryDecision,
)


class StaticDecisionKeys:
    def __init__(self, keys: dict[str, bytes], active_key: str | None) -> None:
        self._keys = keys
        self._active_key = active_key

    def get(self, key_id: str) -> bytes | None:
        return self._keys.get(key_id)

    def active(self) -> tuple[str, bytes] | None:
        if self._active_key is None:
            return None
        return self._active_key, self._keys[self._active_key]


def test_signed_boundary_decision_verifies_against_report() -> None:
    report = BoundaryPreflightReport(
        "local-witness", "CONTINUE_SYNTHETIC", (), False
    )
    keys = StaticDecisionKeys({"decision-1": b"decision-secret"}, "decision-1")
    signed = SignedBoundaryDecision.from_report(report, keys)

    signed.verify(report, keys)
    assert signed.production_enabled is False


def test_signed_boundary_decision_rejects_tampering_and_unknown_key() -> None:
    report = BoundaryPreflightReport(
        "receipt-evidence", "REFACTOR", ("protected_identity",), False
    )
    keys = StaticDecisionKeys({"decision-1": b"decision-secret"}, "decision-1")
    signed = SignedBoundaryDecision.from_report(report, keys)

    with pytest.raises(BoundaryDecisionError, match="match"):
        signed.verify(replace(report, blockers=()), keys)

    unknown_keys = StaticDecisionKeys({"other": b"other-secret"}, "other")
    with pytest.raises(BoundaryDecisionError, match="trusted"):
        signed.verify(report, unknown_keys)


def test_signed_boundary_decision_rejects_production_state() -> None:
    report = BoundaryPreflightReport("local-witness", "CONTINUE_SYNTHETIC", (), False)
    keys = StaticDecisionKeys({"decision-1": b"decision-secret"}, "decision-1")
    forged = SignedBoundaryDecision.from_report(report, keys)
    forged = replace(forged, production_enabled=True)

    with pytest.raises(BoundaryDecisionError, match="signature"):
        forged.verify(report, keys)


def test_signed_boundary_decision_requires_active_key() -> None:
    report = BoundaryPreflightReport("local-witness", "CONTINUE_SYNTHETIC", (), False)
    keys = StaticDecisionKeys({"decision-1": b"decision-secret"}, None)

    with pytest.raises(BoundaryDecisionError, match="active"):
        SignedBoundaryDecision.from_report(report, keys)
