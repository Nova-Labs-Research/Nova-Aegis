"""Deterministic synthetic production-boundary preflight."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


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
