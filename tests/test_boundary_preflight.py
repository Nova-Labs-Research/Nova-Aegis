from __future__ import annotations

import pytest

from nova_aegis import BoundaryGateError, SyntheticBoundaryPreflight


def test_preflight_reports_refactor_blockers_without_enabling_production() -> None:
    report = SyntheticBoundaryPreflight().assess(
        "receipt-evidence",
        {
            "protected_identity": False,
            "durable_witness_retention": False,
            "human_approval": True,
        },
    )

    assert report.decision == "REFACTOR"
    assert report.blockers == ("durable_witness_retention", "protected_identity")
    assert report.production_enabled is False


def test_preflight_can_continue_synthetic_boundary() -> None:
    report = SyntheticBoundaryPreflight().assess(
        "local-witness",
        {"offline": True, "human_approval": True},
    )

    assert report.decision == "CONTINUE_SYNTHETIC"
    assert report.blockers == ()
    assert report.production_enabled is False


def test_preflight_requires_boundary_and_controls() -> None:
    preflight = SyntheticBoundaryPreflight()
    with pytest.raises(ValueError, match="Boundary name"):
        preflight.assess("", {"offline": True})
    with pytest.raises(ValueError, match="controls"):
        preflight.assess("local-witness", {})


def test_preflight_enforcement_rejects_blockers_and_production() -> None:
    preflight = SyntheticBoundaryPreflight()
    blocked = preflight.assess("receipt-evidence", {"protected_identity": False})
    with pytest.raises(BoundaryGateError, match="refactor"):
        preflight.enforce(blocked)

    ready = preflight.assess("local-witness", {"offline": True})
    preflight.enforce(ready)
    with pytest.raises(BoundaryGateError, match="Production"):
        preflight.enforce(ready, requested_mode="production")

    with pytest.raises(ValueError, match="mode"):
        preflight.enforce(ready, requested_mode="unknown")
