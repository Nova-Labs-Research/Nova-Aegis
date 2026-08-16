from __future__ import annotations

from dataclasses import replace
import sqlite3

import pytest

from nova_aegis import (
    LocalJournalKeyProvider,
    LocalSyntheticEvidenceWitness,
    SQLiteSyntheticEvidenceStore,
    SQLiteSyntheticEvidenceWitnessStore,
    SyntheticEvidenceWitnessArbiter,
    SyntheticEvidenceWitnessError,
)


def _record(tmp_path, evidence_id: str = "transcript-1"):
    evidence_store = SQLiteSyntheticEvidenceStore(
        sqlite3.connect(tmp_path / "evidence.db"),
        LocalJournalKeyProvider({"evidence-key": b"evidence-secret"}),
    )
    return evidence_store.append(evidence_id, "transcript", {"valid": True})


def _witnesses():
    return {
        "witness-a": LocalSyntheticEvidenceWitness("witness-a", b"witness-a-secret"),
        "witness-b": LocalSyntheticEvidenceWitness("witness-b", b"witness-b-secret"),
    }


def test_distinct_witness_persists_and_verifies_from_separate_store(tmp_path) -> None:
    record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("witness-a", b"witness-secret")
    attestation = witness.attest(record, evaluator_id="evaluator")
    witness_database = tmp_path / "witness.db"
    store = SQLiteSyntheticEvidenceWitnessStore(sqlite3.connect(witness_database))
    store.register(attestation)

    reopened = SQLiteSyntheticEvidenceWitnessStore(sqlite3.connect(witness_database))
    persisted = reopened.load(record.evidence_id, witness.witness_id)

    witness.verify(persisted, record, evaluator_id="evaluator")
    assert persisted.evidence_digest == record.digest


def test_self_witnessing_is_refused(tmp_path) -> None:
    record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("evaluator", b"witness-secret")

    with pytest.raises(SyntheticEvidenceWitnessError, match="distinct"):
        witness.attest(record, evaluator_id="evaluator")


def test_evidence_substitution_and_signature_tampering_are_refused(tmp_path) -> None:
    record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("witness-a", b"witness-secret")
    attestation = witness.attest(record, evaluator_id="evaluator")

    substituted = replace(record, digest="0" * 64)
    with pytest.raises(SyntheticEvidenceWitnessError, match="binding"):
        witness.verify(attestation, substituted, evaluator_id="evaluator")
    with pytest.raises(SyntheticEvidenceWitnessError, match="signature"):
        witness.verify(replace(attestation, signature="0" * 64), record, evaluator_id="evaluator")


def test_distinct_verified_quorum_is_required(tmp_path) -> None:
    record = _record(tmp_path)
    witnesses = _witnesses()
    attestations = tuple(
        witness.attest(record, evaluator_id="evaluator")
        for witness in witnesses.values()
    )

    decision = SyntheticEvidenceWitnessArbiter().decide(
        record,
        attestations,
        witnesses,
        evaluator_id="evaluator",
    )

    assert decision.witness_ids == ("witness-a", "witness-b")
    assert decision.required_witnesses == 2


def test_duplicate_unknown_and_insufficient_witnesses_fail_closed(tmp_path) -> None:
    record = _record(tmp_path)
    witnesses = _witnesses()
    first = witnesses["witness-a"].attest(record, evaluator_id="evaluator")
    arbiter = SyntheticEvidenceWitnessArbiter()

    with pytest.raises(SyntheticEvidenceWitnessError, match="duplicate"):
        arbiter.decide(record, (first, first), witnesses, evaluator_id="evaluator")
    with pytest.raises(SyntheticEvidenceWitnessError, match="insufficient"):
        arbiter.decide(record, (first,), witnesses, evaluator_id="evaluator")
    with pytest.raises(SyntheticEvidenceWitnessError, match="unknown"):
        arbiter.decide(
            record,
            (replace(first, witness_id="unknown"),),
            witnesses,
            evaluator_id="evaluator",
            minimum_witnesses=1,
        )


def test_conflicting_and_missing_persisted_attestations_fail_closed(tmp_path) -> None:
    record = _record(tmp_path)
    witness = LocalSyntheticEvidenceWitness("witness-a", b"witness-secret")
    attestation = witness.attest(record, evaluator_id="evaluator")
    store = SQLiteSyntheticEvidenceWitnessStore(sqlite3.connect(tmp_path / "witness.db"))
    store.register(attestation)

    with pytest.raises(SyntheticEvidenceWitnessError, match="conflicting"):
        store.register(replace(attestation, signature="0" * 64))
    with pytest.raises(SyntheticEvidenceWitnessError, match="missing"):
        store.load("missing", "witness-a")