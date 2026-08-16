from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from nova_aegis import (
    AnchoredSQLiteSyntheticEvidenceStore,
    LocalJournalKeyProvider,
    LocalSyntheticEvidenceWitness,
    SQLiteSyntheticEvidenceAnchorStore,
    SQLiteSyntheticEvidenceWitnessStore,
    SyntheticEvidenceError,
    SyntheticEvidenceWitnessArbiter,
    SyntheticEvidenceWitnessError,
)


def _store(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    anchor_store = SQLiteSyntheticEvidenceAnchorStore(
        sqlite3.connect(tmp_path / "anchors.db"),
        LocalJournalKeyProvider({"anchor-key": b"anchor-secret"}),
    )
    return AnchoredSQLiteSyntheticEvidenceStore(
        sqlite3.connect(tmp_path / "evidence.db"),
        LocalJournalKeyProvider({"evidence-key": b"evidence-secret"}),
        store_id="evaluation-store",
        anchor_store=anchor_store,
    )


def _record(tmp_path, evidence_id: str = "transcript-1"):
    store = _store(tmp_path)
    return store, store.append(evidence_id, "transcript", {"valid": True})


def _witnesses():
    return {
        "witness-a": LocalSyntheticEvidenceWitness("witness-a", b"witness-a-secret"),
        "witness-b": LocalSyntheticEvidenceWitness("witness-b", b"witness-b-secret"),
    }


def test_distinct_witness_persists_and_verifies_from_separate_store(tmp_path) -> None:
    evidence_store, record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("witness-a", b"witness-secret")
    attestation = witness.attest(
        record.evidence_id,
        evidence_store=evidence_store,
        evaluator_id="evaluator",
    )
    witness_database = tmp_path / "witness.db"
    store = SQLiteSyntheticEvidenceWitnessStore(sqlite3.connect(witness_database))
    store.register(attestation)

    reopened = SQLiteSyntheticEvidenceWitnessStore(sqlite3.connect(witness_database))
    persisted = reopened.load(record.evidence_id, witness.witness_id)

    witness.verify(
        persisted,
        evidence_store=evidence_store,
        evaluator_id="evaluator",
    )
    assert persisted.evidence_digest == record.digest
    assert persisted.store_id == "evaluation-store"


def test_self_witnessing_is_refused(tmp_path) -> None:
    evidence_store, record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("evaluator", b"witness-secret")

    with pytest.raises(SyntheticEvidenceWitnessError, match="distinct"):
        witness.attest(
            record.evidence_id,
            evidence_store=evidence_store,
            evaluator_id="evaluator",
        )


def test_evidence_substitution_and_signature_tampering_are_refused(tmp_path) -> None:
    evidence_store, record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("witness-a", b"witness-secret")
    attestation = witness.attest(
        record.evidence_id,
        evidence_store=evidence_store,
        evaluator_id="evaluator",
    )

    connection = sqlite3.connect(tmp_path / "evidence.db")
    connection.execute(
        "UPDATE synthetic_evidence_events SET payload_json = '{\"valid\":false}'"
    )
    connection.commit()
    with pytest.raises(SyntheticEvidenceError):
        witness.verify(
            attestation,
            evidence_store=evidence_store,
            evaluator_id="evaluator",
        )

    clean_store, clean_record = _record(tmp_path / "clean")
    clean_attestation = witness.attest(
        clean_record.evidence_id,
        evidence_store=clean_store,
        evaluator_id="evaluator",
    )
    with pytest.raises(SyntheticEvidenceWitnessError, match="signature"):
        witness.verify(
            replace(clean_attestation, signature="0" * 64),
            evidence_store=clean_store,
            evaluator_id="evaluator",
        )


def test_unpersisted_evidence_cannot_be_attested(tmp_path) -> None:
    evidence_store = _store(tmp_path)
    witness = LocalSyntheticEvidenceWitness("witness-a", b"witness-secret")

    with pytest.raises(SyntheticEvidenceError, match="missing"):
        witness.attest(
            "constructed-record",
            evidence_store=evidence_store,
            evaluator_id="evaluator",
        )


def test_distinct_verified_quorum_is_required(tmp_path) -> None:
    evidence_store, record = _record(tmp_path)
    witnesses = _witnesses()
    attestations = tuple(
        witness.attest(
            record.evidence_id,
            evidence_store=evidence_store,
            evaluator_id="evaluator",
        )
        for witness in witnesses.values()
    )

    decision = SyntheticEvidenceWitnessArbiter().decide(
        record.evidence_id,
        attestations,
        witnesses,
        evidence_store=evidence_store,
        evaluator_id="evaluator",
    )

    assert decision.witness_ids == ("witness-a", "witness-b")
    assert decision.required_witnesses == 2


def test_duplicate_unknown_and_insufficient_witnesses_fail_closed(tmp_path) -> None:
    evidence_store, record = _record(tmp_path)
    witnesses = _witnesses()
    first = witnesses["witness-a"].attest(
        record.evidence_id,
        evidence_store=evidence_store,
        evaluator_id="evaluator",
    )
    arbiter = SyntheticEvidenceWitnessArbiter()

    with pytest.raises(SyntheticEvidenceWitnessError, match="duplicate"):
        arbiter.decide(
            record.evidence_id,
            (first, first),
            witnesses,
            evidence_store=evidence_store,
            evaluator_id="evaluator",
        )
    with pytest.raises(SyntheticEvidenceWitnessError, match="insufficient"):
        arbiter.decide(
            record.evidence_id,
            (first,),
            witnesses,
            evidence_store=evidence_store,
            evaluator_id="evaluator",
        )
    with pytest.raises(SyntheticEvidenceWitnessError, match="unknown"):
        arbiter.decide(
            record.evidence_id,
            (replace(first, witness_id="unknown"),),
            witnesses,
            evidence_store=evidence_store,
            evaluator_id="evaluator",
            minimum_witnesses=1,
        )


def test_conflicting_and_missing_persisted_attestations_fail_closed(tmp_path) -> None:
    evidence_store, record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("witness-a", b"witness-secret")
    attestation = witness.attest(
        record.evidence_id,
        evidence_store=evidence_store,
        evaluator_id="evaluator",
    )
    store = SQLiteSyntheticEvidenceWitnessStore(sqlite3.connect(tmp_path / "witness.db"))
    store.register(attestation)

    with pytest.raises(SyntheticEvidenceWitnessError, match="conflicting"):
        store.register(replace(attestation, signature="0" * 64))
    with pytest.raises(SyntheticEvidenceWitnessError, match="missing"):
        store.load("missing", "witness-a")