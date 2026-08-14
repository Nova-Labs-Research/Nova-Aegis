from __future__ import annotations

import pytest

from nova_aegis import (
    SyntheticBoundaryError,
    SyntheticBoundaryManifest,
    SyntheticNestedBoundary,
)


def _boundary() -> SyntheticNestedBoundary:
    return SyntheticNestedBoundary(
        SyntheticBoundaryManifest("phase-91-inner", ("echo",))
    )


def test_nested_boundary_allows_only_manifested_benign_capability() -> None:
    boundary = _boundary()
    boundary.start()

    result = boundary.execute("echo", "echo", {"value": "synthetic"})

    assert result.boundary_id == "phase-91-inner"
    assert result.value == {"value": "synthetic"}


def test_nested_boundary_rejects_unavailable_or_ungranted_operations() -> None:
    boundary = _boundary()
    with pytest.raises(SyntheticBoundaryError, match="unavailable"):
        boundary.execute("echo", "echo")

    boundary.start()
    with pytest.raises(SyntheticBoundaryError, match="not granted"):
        boundary.execute("filesystem", "echo")
    with pytest.raises(SyntheticBoundaryError, match="not allowed"):
        boundary.execute("echo", "read")


def test_nested_boundary_rejects_host_filesystem_network_and_production_requests() -> None:
    boundary = _boundary()
    for request in (
        boundary.request_host_access,
        boundary.request_filesystem_access,
        boundary.request_network_access,
        boundary.request_production,
    ):
        with pytest.raises(SyntheticBoundaryError):
            request()


def test_nested_boundary_teardown_is_observable_and_stops_execution() -> None:
    boundary = _boundary()
    boundary.start()
    assert boundary.active is True

    boundary.teardown()

    assert boundary.active is False
    with pytest.raises(SyntheticBoundaryError, match="unavailable"):
        boundary.execute("echo", "echo")


def test_manifest_rejects_unsafe_or_ambiguous_boundary_configuration() -> None:
    with pytest.raises(ValueError, match="host"):
        SyntheticBoundaryManifest("unsafe", ("echo",), host_access_allowed=True)
    with pytest.raises(ValueError, match="unique"):
        SyntheticBoundaryManifest("duplicate", ("echo", "echo"))
    with pytest.raises(ValueError, match="production"):
        SyntheticBoundaryManifest("production", ("echo",), production_enabled=True)
