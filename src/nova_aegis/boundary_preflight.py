"""Deterministic synthetic production-boundary preflight."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class BoundaryGateError(RuntimeError):
    """Raised when a boundary preflight cannot authorize the requested mode."""


@dataclass(frozen=True)
class BoundaryPreflightReport:
    boundary: str
    decision: str
    blockers: tuple[str, ...]
    production_enabled: bool = False


class SyntheticBoundaryPreflight:
    """Report missing controls without enabling any production boundary."""

    def assess(
        self,
        boundary: str,
        controls: Mapping[str, bool],
    ) -> BoundaryPreflightReport:
        if not boundary.strip():
            raise ValueError("Boundary name is required")
        if not controls:
            raise ValueError("Boundary controls are required")
        blockers = tuple(sorted(name for name, satisfied in controls.items() if not satisfied))
        return BoundaryPreflightReport(
            boundary=boundary,
            decision="REFACTOR" if blockers else "CONTINUE_SYNTHETIC",
            blockers=blockers,
            production_enabled=False,
        )

    def enforce(
        self,
        report: BoundaryPreflightReport,
        *,
        requested_mode: str = "synthetic",
    ) -> None:
        if requested_mode not in {"synthetic", "production"}:
            raise ValueError("Boundary mode must be synthetic or production")
        if requested_mode == "production" or report.production_enabled:
            raise BoundaryGateError("Production boundary enablement is blocked")
        if report.decision != "CONTINUE_SYNTHETIC" or report.blockers:
            raise BoundaryGateError(
                f"Boundary requires refactor: {', '.join(report.blockers) or 'unknown blocker'}"
            )
