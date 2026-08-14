"""Benign nested boundary model for synthetic containment evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class SyntheticBoundaryError(RuntimeError):
    """Raised when a synthetic boundary contract is violated."""


@dataclass(frozen=True)
class SyntheticBoundaryManifest:
    boundary_id: str
    allowed_capabilities: tuple[str, ...]
    host_access_allowed: bool = False
    filesystem_access_allowed: bool = False
    network_access_allowed: bool = False
    production_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.boundary_id.strip():
            raise ValueError("Synthetic boundary ID is required")
        if len(set(self.allowed_capabilities)) != len(self.allowed_capabilities):
            raise ValueError("Synthetic boundary capabilities must be unique")
        if self.host_access_allowed or self.filesystem_access_allowed or self.network_access_allowed:
            raise ValueError("Synthetic boundary cannot allow host, filesystem, or network access")
        if self.production_enabled:
            raise ValueError("Synthetic boundary cannot enable production")


@dataclass(frozen=True)
class SyntheticBoundaryResult:
    boundary_id: str
    capability: str
    operation: str
    value: Any


class SyntheticNestedBoundary:
    """Process-local inner boundary model; this is not OS-level isolation."""

    def __init__(self, manifest: SyntheticBoundaryManifest) -> None:
        self.manifest = manifest
        self._active = False

    def start(self) -> None:
        if self._active:
            raise SyntheticBoundaryError("Synthetic boundary is already active")
        self._active = True

    def execute(
        self,
        capability: str,
        operation: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> SyntheticBoundaryResult:
        if not self._active:
            raise SyntheticBoundaryError("Synthetic boundary is unavailable")
        if capability not in self.manifest.allowed_capabilities:
            raise SyntheticBoundaryError("Synthetic capability is not granted")
        if operation != "echo":
            raise SyntheticBoundaryError("Synthetic operation is not allowed")
        return SyntheticBoundaryResult(
            self.manifest.boundary_id,
            capability,
            operation,
            dict(parameters or {}),
        )

    def request_host_access(self) -> None:
        raise SyntheticBoundaryError("Synthetic boundary cannot access the host")

    def request_filesystem_access(self) -> None:
        raise SyntheticBoundaryError("Synthetic boundary cannot access the real filesystem")

    def request_network_access(self) -> None:
        raise SyntheticBoundaryError("Synthetic boundary cannot access the network")

    def request_production(self) -> None:
        raise SyntheticBoundaryError("Synthetic boundary cannot enable production")

    def teardown(self) -> None:
        self._active = False

    @property
    def active(self) -> bool:
        return self._active
