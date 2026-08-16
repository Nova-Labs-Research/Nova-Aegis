"""Independent local witness boundary for authenticated synthetic evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import sqlite3
from typing import Mapping

from .evidence_anchor import AnchoredSQLiteSyntheticEvidenceStore


class SyntheticEvidenceWitnessError(RuntimeError):
    """Raised when synthetic evidence witness state cannot be trusted."""


@dataclass(frozen=True)
class SyntheticEvidenceWitnessAttestation:
    evidence_id: str
    evidence_sequence: int
    evidence_type: str
    evidence_digest: str
    store_id: str
    anchor_event_count: int
    anchor_terminal_digest: str
    anchor_signature: str
    evaluator_id: str
    witness_id: str
    signature: str

    def payload(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "evidence_sequence": self.evidence_sequence,
            "evidence_type": self.evidence_type,
            "evidence_digest": self.evidence_digest,
            "store_id": self.store_id,
            "anchor_event_count": self.anchor_event_count,
            "anchor_terminal_digest": self.anchor_terminal_digest,
            "anchor_signature": self.anchor_signature,
            "evaluator_id": self.evaluator_id,
            "witness_id": self.witness_id,
        }


@dataclass(frozen=True)
class SyntheticEvidenceWitnessDecision:
    evidence_id: str
    witness_ids: tuple[str, ...]
    required_witnesses: int


class LocalSyntheticEvidenceWitness:
    """Distinct local signer; its key is not shared with the evidence store."""

    def __init__(self, witness_id: str, secret: bytes) -> None:
        if not witness_id.strip() or not secret:
            raise ValueError("Synthetic evidence witness identity and secret are required")
        self.witness_id = witness_id
        self._secret = bytes(secret)
        self._attestations: dict[str, SyntheticEvidenceWitnessAttestation] = {}

    def attest(
        self,
        evidence_id: str,
        *,
        evidence_store: AnchoredSQLiteSyntheticEvidenceStore,
        evaluator_id: str,
    ) -> SyntheticEvidenceWitnessAttestation:
        if not evaluator_id.strip():
            raise ValueError("Synthetic evidence evaluator identity is required")
        if evaluator_id == self.witness_id:
            raise SyntheticEvidenceWitnessError("Evaluator and witness must be distinct")
        record, anchor = evidence_store.get_verified(evidence_id)
        unsigned = SyntheticEvidenceWitnessAttestation(
            record.evidence_id,
            record.sequence,
            record.evidence_type,
            record.digest,
            evidence_store.store_id,
            anchor.event_count,
            anchor.terminal_digest,
            anchor.signature,
            evaluator_id,
            self.witness_id,
            "",
        )
        attestation = SyntheticEvidenceWitnessAttestation(
            **unsigned.payload(),
            signature=self._sign(unsigned.payload()),
        )
        existing = self._attestations.get(record.evidence_id)
        if existing is not None and existing != attestation:
            raise SyntheticEvidenceWitnessError("Synthetic evidence witness conflict")
        self._attestations[record.evidence_id] = attestation
        return attestation

    def verify(
        self,
        attestation: SyntheticEvidenceWitnessAttestation,
        *,
        evidence_store: AnchoredSQLiteSyntheticEvidenceStore,
        evaluator_id: str,
    ) -> None:
        record, anchor = evidence_store.get_verified(attestation.evidence_id)
        expected_fields = (
            record.evidence_id,
            record.sequence,
            record.evidence_type,
            record.digest,
            evidence_store.store_id,
            anchor.event_count,
            anchor.terminal_digest,
            anchor.signature,
            evaluator_id,
            self.witness_id,
        )
        actual_fields = (
            attestation.evidence_id,
            attestation.evidence_sequence,
            attestation.evidence_type,
            attestation.evidence_digest,
            attestation.store_id,
            attestation.anchor_event_count,
            attestation.anchor_terminal_digest,
            attestation.anchor_signature,
            attestation.evaluator_id,
            attestation.witness_id,
        )
        if actual_fields != expected_fields:
            raise SyntheticEvidenceWitnessError("Synthetic evidence witness binding is invalid")
        if evaluator_id == self.witness_id:
            raise SyntheticEvidenceWitnessError("Evaluator and witness must be distinct")
        expected_signature = self._sign(attestation.payload())
        if not hmac.compare_digest(attestation.signature, expected_signature):
            raise SyntheticEvidenceWitnessError("Synthetic evidence witness signature is invalid")

    def _sign(self, payload: Mapping[str, object]) -> str:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hmac.new(self._secret, serialized, hashlib.sha256).hexdigest()


class SyntheticEvidenceWitnessArbiter:
    """Requires a verified quorum of distinct local evidence witnesses."""

    def decide(
        self,
        evidence_id: str,
        attestations: tuple[SyntheticEvidenceWitnessAttestation, ...],
        witnesses: Mapping[str, LocalSyntheticEvidenceWitness],
        *,
        evidence_store: AnchoredSQLiteSyntheticEvidenceStore,
        evaluator_id: str,
        minimum_witnesses: int = 2,
    ) -> SyntheticEvidenceWitnessDecision:
        if minimum_witnesses < 1:
            raise ValueError("Synthetic evidence witness quorum must be positive")
        verified: list[str] = []
        for attestation in attestations:
            witness = witnesses.get(attestation.witness_id)
            if witness is None:
                raise SyntheticEvidenceWitnessError("Synthetic evidence witness is unknown")
            if attestation.witness_id in verified:
                raise SyntheticEvidenceWitnessError("Synthetic evidence witness quorum contains a duplicate")
            if attestation.evidence_id != evidence_id:
                raise SyntheticEvidenceWitnessError("Synthetic evidence witness binding is invalid")
            witness.verify(
                attestation,
                evidence_store=evidence_store,
                evaluator_id=evaluator_id,
            )
            verified.append(attestation.witness_id)
        if len(verified) < minimum_witnesses:
            raise SyntheticEvidenceWitnessError("Synthetic evidence witness quorum is insufficient")
        return SyntheticEvidenceWitnessDecision(
            evidence_id,
            tuple(sorted(verified)),
            minimum_witnesses,
        )


class SQLiteSyntheticEvidenceWitnessStore:
    """Separate append-only local store for witness attestations."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_evidence_witness_attestations (
                evidence_id TEXT NOT NULL,
                witness_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                PRIMARY KEY (evidence_id, witness_id)
            )
            """
        )
        self._connection.commit()

    def register(self, attestation: SyntheticEvidenceWitnessAttestation) -> None:
        current = self._current(attestation.evidence_id, attestation.witness_id)
        if current is not None and current != attestation:
            raise SyntheticEvidenceWitnessError("Synthetic evidence witness has conflicting attestations")
        if current == attestation:
            return
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO synthetic_evidence_witness_attestations(
                    evidence_id, witness_id, payload
                ) VALUES (?, ?, ?)
                """,
                (
                    attestation.evidence_id,
                    attestation.witness_id,
                    _attestation_payload(attestation),
                ),
            )

    def load(
        self,
        evidence_id: str,
        witness_id: str,
    ) -> SyntheticEvidenceWitnessAttestation:
        attestation = self._current(evidence_id, witness_id)
        if attestation is None:
            raise SyntheticEvidenceWitnessError("Synthetic evidence witness attestation is missing")
        return attestation

    def _current(
        self,
        evidence_id: str,
        witness_id: str,
    ) -> SyntheticEvidenceWitnessAttestation | None:
        row = self._connection.execute(
            """
            SELECT payload FROM synthetic_evidence_witness_attestations
            WHERE evidence_id = ? AND witness_id = ?
            """,
            (evidence_id, witness_id),
        ).fetchone()
        if row is None:
            return None
        return _attestation_from_payload(row[0])


def _attestation_payload(attestation: SyntheticEvidenceWitnessAttestation) -> str:
    return json.dumps(
        {**attestation.payload(), "signature": attestation.signature},
        sort_keys=True,
        separators=(",", ":"),
    )


def _attestation_from_payload(payload: str) -> SyntheticEvidenceWitnessAttestation:
    try:
        value = json.loads(payload)
        return SyntheticEvidenceWitnessAttestation(
            evidence_id=str(value["evidence_id"]),
            evidence_sequence=int(value["evidence_sequence"]),
            evidence_type=str(value["evidence_type"]),
            evidence_digest=str(value["evidence_digest"]),
            store_id=str(value["store_id"]),
            anchor_event_count=int(value["anchor_event_count"]),
            anchor_terminal_digest=str(value["anchor_terminal_digest"]),
            anchor_signature=str(value["anchor_signature"]),
            evaluator_id=str(value["evaluator_id"]),
            witness_id=str(value["witness_id"]),
            signature=str(value["signature"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise SyntheticEvidenceWitnessError("Synthetic evidence witness attestation is malformed") from error