from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from nova_aegis import (
    ExternalReceiptError,
    LocalExternalReceiptRegistry,
    LocalReceiptWitness,
    SQLiteReceiptWitnessStore,
    SyntheticWitnessArbiter,
)


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


def test_witness_store_replays_after_reopen_and_rejects_revocation(tmp_path) -> None:
    receipt = _receipt()
    witness = LocalReceiptWitness(witness_id="witness-1", secret=b"witness-secret")
    attestation = witness.attest(receipt, issuer_id="issuer-1")
    database_path = tmp_path / "witness.sqlite3"
    connection = sqlite3.connect(database_path)
    store = SQLiteReceiptWitnessStore(connection)
    store.register(attestation)
    connection.close()
    connection = sqlite3.connect(database_path)
    store = SQLiteReceiptWitnessStore(connection)
    store.verify(receipt, witness, issuer_id="issuer-1")
    assert store.load(receipt.receipt_id) == attestation

    store.revoke(receipt.receipt_id)
    with pytest.raises(ExternalReceiptError, match="revoked"):
        store.verify(receipt, witness, issuer_id="issuer-1")


def test_witness_store_rejects_conflicting_duplicate_attestation() -> None:
    receipt = _receipt()
    witness = LocalReceiptWitness(witness_id="witness-1", secret=b"witness-secret")
    attestation = witness.attest(receipt, issuer_id="issuer-1")
    connection = sqlite3.connect(":memory:")
    store = SQLiteReceiptWitnessStore(connection)
    store.register(attestation)

    with pytest.raises(ExternalReceiptError, match="conflicting"):
        store.register(replace(attestation, issuer_id="forged-issuer"))


def test_witness_arbiter_requires_distinct_verified_quorum() -> None:
    receipt = _receipt()
    first = LocalReceiptWitness(witness_id="witness-1", secret=b"witness-secret-1")
    second = LocalReceiptWitness(witness_id="witness-2", secret=b"witness-secret-2")
    first_attestation = first.attest(receipt, issuer_id="issuer-1")
    second_attestation = second.attest(receipt, issuer_id="issuer-1")

    decision = SyntheticWitnessArbiter().decide(
        receipt,
        (first_attestation, second_attestation),
        {"witness-1": first, "witness-2": second},
        issuer_id="issuer-1",
    )
    assert decision.witness_ids == ("witness-1", "witness-2")

    with pytest.raises(ExternalReceiptError, match="insufficient"):
        SyntheticWitnessArbiter().decide(
            receipt,
            (first_attestation,),
            {"witness-1": first},
            issuer_id="issuer-1",
        )

    with pytest.raises(ExternalReceiptError, match="duplicate"):
        SyntheticWitnessArbiter().decide(
            receipt,
            (first_attestation, first_attestation),
            {"witness-1": first},
            minimum_witnesses=1,
            issuer_id="issuer-1",
        )
