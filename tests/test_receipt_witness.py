from __future__ import annotations

from dataclasses import replace

import pytest

from nova_aegis import ExternalReceiptError, LocalExternalReceiptRegistry, LocalReceiptWitness


def _receipt():
    issuer = LocalExternalReceiptRegistry(secret=b"issuer-secret")
    return issuer.create(
        task_id="task-1",
        tool_name="synthetic-status",
        user_id="operator-1",
        audience="local-gateway",
        status="completed",
        parameters_hash="params-1",
        result={"status": "ok"},
    )


def test_separate_witness_attests_and_verifies_receipt() -> None:
    receipt = _receipt()
    witness = LocalReceiptWitness(witness_id="witness-1", secret=b"witness-secret")

    attestation = witness.attest(receipt, issuer_id="issuer-1")
    witness.verify(attestation, receipt, issuer_id="issuer-1")
    assert attestation.witness_id != attestation.issuer_id


def test_witness_rejects_self_witness_and_tampered_receipt() -> None:
    receipt = _receipt()
    witness = LocalReceiptWitness(witness_id="witness-1", secret=b"witness-secret")

    with pytest.raises(ExternalReceiptError, match="distinct"):
        witness.attest(receipt, issuer_id="witness-1")

    attestation = witness.attest(receipt, issuer_id="issuer-1")
    forged = replace(receipt, result_hash="forged-result")
    with pytest.raises(ExternalReceiptError, match="digest"):
        witness.verify(attestation, forged, issuer_id="issuer-1")


def test_different_witness_key_rejects_attestation() -> None:
    receipt = _receipt()
    witness = LocalReceiptWitness(witness_id="witness-1", secret=b"witness-secret")
    other_witness = LocalReceiptWitness(witness_id="witness-1", secret=b"other-secret")
    attestation = witness.attest(receipt, issuer_id="issuer-1")

    with pytest.raises(ExternalReceiptError, match="signature"):
        other_witness.verify(attestation, receipt, issuer_id="issuer-1")
