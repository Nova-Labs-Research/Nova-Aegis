from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import uuid

import pytest


ROOT = Path(__file__).parents[1]
PROJECT = ROOT / "t1" / "signer" / "NovaAegis.ProtectedSigner"
DLL = PROJECT / "bin" / "Release" / "net10.0-windows" / "NovaAegis.ProtectedSigner.dll"


@pytest.fixture(scope="module", autouse=True)
def build_candidate() -> None:
    result = subprocess.run(
        ["dotnet", "build", str(PROJECT), "--configuration", "Release", "--nologo"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _request(**changes: object) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    value: dict[str, object] = {
        "protocol": "nova-aegis-protected-signer",
        "schema_version": 1,
        "purpose": "nova-aegis.evidence-anchor.v1",
        "environment": "t1-pilot-offline",
        "boundary_id": "g1-candidate-test",
        "caller_id": "nova-aegis-runtime",
        "request_id": str(uuid.uuid4()),
        "nonce": "A" * 22,
        "issued_at": now.isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "expires_at": (now + timedelta(seconds=20)).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        "policy_version": "t1-policy-v1",
        "invariant_version": "inv-trajectory-v1",
        "payload_digest": "sha256:" + "0" * 64,
        "signer_identity": "nova-aegis-t1-anchor-signer",
        "key_version": "v1",
        "audit_correlation_id": str(uuid.uuid4()),
    }
    value.update(changes)
    return value


def _validate(payload: object) -> tuple[int, dict[str, object]]:
    result = subprocess.run(
        ["dotnet", str(DLL), "--validate-request"],
        input=json.dumps(payload, separators=(",", ":")),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def test_valid_allowlisted_envelope_is_canonicalized() -> None:
    code, result = _validate(_request())
    assert code == 0
    assert result["Valid"] is True
    assert result["Code"] == "VALID"
    assert len(str(result["EnvelopeDigest"])) == 64


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("purpose", "generic.sign", "PURPOSE_REFUSED"),
        ("environment", "production", "CALLER_UNAUTHORIZED"),
        ("caller_id", "reasoning", "CALLER_UNAUTHORIZED"),
        ("signer_identity", "substitute", "IDENTITY_MISMATCH"),
        ("key_version", "v2", "KEY_VERSION_MISMATCH"),
    ],
)
def test_boundary_substitution_is_refused(field: str, value: object, expected: str) -> None:
    code, result = _validate(_request(**{field: value}))
    assert code == 2
    assert result["Code"] == expected


def test_unknown_missing_and_malformed_fields_are_refused() -> None:
    unknown = _request(extra="not-allowed")
    missing = _request()
    del missing["nonce"]
    for payload in (unknown, missing, ["not", "an", "object"]):
        code, result = _validate(payload)
        assert code == 2
        assert result["Code"] == "SCHEMA_INVALID"


def test_duplicate_json_key_is_refused() -> None:
    payload = json.dumps(_request(), separators=(",", ":"))
    duplicate = payload[:-1] + ',"purpose":"nova-aegis.evidence-anchor.v1"}'
    result = subprocess.run(
        ["dotnet", str(DLL), "--validate-request"],
        input=duplicate,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["Code"] == "SCHEMA_INVALID"


def test_expired_and_excessive_lifetime_are_refused() -> None:
    now = datetime.now(timezone.utc)
    expired = _request(
        issued_at=(now - timedelta(seconds=20)).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        expires_at=(now - timedelta(seconds=1)).isoformat(timespec="microseconds").replace("+00:00", "Z"),
    )
    excessive = _request(
        expires_at=(now + timedelta(minutes=5)).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )
    for payload in (expired, excessive):
        code, result = _validate(payload)
        assert code == 2
        assert result["Code"] == "REQUEST_EXPIRED"


def test_candidate_has_no_activation_mode_or_key_creation_path() -> None:
    result = subprocess.run(
        ["dotnet", str(DLL)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 3
    assert "BLOCK_IMPLEMENTATION" in result.stderr

    sources = "\n".join(path.read_text(encoding="utf-8") for path in PROJECT.glob("*.cs"))
    assert "CngKey.Create" not in sources
    assert "TcpListener" not in sources
    assert "HttpListener" not in sources


def test_candidate_manifest_is_non_authoritative() -> None:
    result = subprocess.run(
        ["dotnet", str(DLL), "--candidate-manifest"],
        capture_output=True,
        text=True,
        check=False,
    )
    manifest = json.loads(result.stdout)
    assert result.returncode == 0
    assert manifest["activation"] == "BLOCKED_G1_CANDIDATE"
    assert manifest["purpose"] == "nova-aegis.evidence-anchor.v1"