"""Synthetic independent-witness boundary for receipt experiments."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import sqlite3
from typing import Mapping

from .receipt_store import ExternalExecutionReceipt, ExternalReceiptError


@dataclass(frozen=True)
class ReceiptWitnessAttestation:
    receipt_id: str
    issuer_id: str
    witness_id: str
    receipt_digest: str
    signature: str


@dataclass(frozen=True)
class WitnessQuorumDecision:
    receipt_id: str
    witness_ids: tuple[str, ...]
    required_witnesses: int


class SyntheticWitnessArbiter:
    """Require distinct local witnesses before accepting a receipt claim."""

    def decide(
        self,
        receipt: ExternalExecutionReceipt,
        attestations: tuple[ReceiptWitnessAttestation, ...],
        witnesses: Mapping[str, LocalReceiptWitness],
        *,
        minimum_witnesses: int = 2,
        issuer_id: str,
    ) -> WitnessQuorumDecision:
        if minimum_witnesses < 1:
            raise ValueError("Witness quorum must be positive")
        verified: list[str] = []
        for attestation in attestations:
            witness = witnesses.get(attestation.witness_id)
            if witness is None:
                raise ExternalReceiptError("Receipt witness is unknown")
            if attestation.witness_id in verified:
                raise ExternalReceiptError("Receipt witness quorum contains a duplicate")
            witness.verify(attestation, receipt, issuer_id=issuer_id)
            verified.append(attestation.witness_id)
        if len(verified) < minimum_witnesses:
            raise ExternalReceiptError("Receipt witness quorum is insufficient")
        return WitnessQuorumDecision(
            receipt.receipt_id,
            tuple(sorted(verified)),
            minimum_witnesses,
        )


class LocalReceiptWitness:
    """Separate local signer used to test receipt-witness separation."""

    def __init__(self, *, witness_id: str, secret: bytes) -> None:
        if not witness_id.strip() or not secret:
            raise ValueError("Receipt witness identity and secret are required")
        self.witness_id = witness_id
        self._secret = secret
        self._attestations: dict[str, ReceiptWitnessAttestation] = {}

    def attest(
        self,
        receipt: ExternalExecutionReceipt,
        *,
        issuer_id: str,
    ) -> ReceiptWitnessAttestation:
        if not issuer_id.strip():
            raise ValueError("Receipt issuer identity is required")
        if issuer_id == self.witness_id:
            raise ExternalReceiptError("Receipt issuer and witness must be distinct")
        receipt_digest = digest_receipt(receipt)
        attestation = ReceiptWitnessAttestation(
            receipt.receipt_id,
            issuer_id,
            self.witness_id,
            receipt_digest,
            self._sign(receipt.receipt_id, issuer_id, self.witness_id, receipt_digest),
        )
        existing = self._attestations.get(receipt.receipt_id)
        if existing is not None and existing != attestation:
            raise ExternalReceiptError("Receipt witness has conflicting attestations")
        self._attestations[receipt.receipt_id] = attestation
        return attestation

    def verify(
        self,
        attestation: ReceiptWitnessAttestation,
        receipt: ExternalExecutionReceipt,
        *,
        issuer_id: str,
    ) -> None:
        if attestation.receipt_id != receipt.receipt_id:
            raise ExternalReceiptError("Receipt witness does not match receipt")
        if attestation.issuer_id != issuer_id:
            raise ExternalReceiptError("Receipt witness issuer does not match")
        if attestation.witness_id != self.witness_id:
            raise ExternalReceiptError("Receipt witness identity does not match")
        if attestation.receipt_digest != digest_receipt(receipt):
            raise ExternalReceiptError("Receipt witness digest does not match")
        expected = self._sign(
            attestation.receipt_id,
            attestation.issuer_id,
            attestation.witness_id,
            attestation.receipt_digest,
        )
        if not hmac.compare_digest(attestation.signature, expected):
            raise ExternalReceiptError("Receipt witness signature is invalid")

    def _sign(self, *parts: str) -> str:
        payload = "|".join(parts).encode("utf-8")
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()


class SQLiteReceiptWitnessStore:
    """Append-only local witness event store for persistence experiments."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS receipt_witness_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def register(self, attestation: ReceiptWitnessAttestation) -> None:
        current = self._current(attestation.receipt_id)
        if current is not None and current != attestation:
            raise ExternalReceiptError("Receipt witness has conflicting attestations")
        if current == attestation:
            return
        self._append("register", attestation.receipt_id, _attestation_payload(attestation))

    def revoke(self, receipt_id: str) -> None:
        current = self._current(receipt_id)
        if current is None:
            raise ExternalReceiptError("Receipt witness attestation is not registered")
        if self._is_revoked(receipt_id):
            return
        self._append("revoke", receipt_id, "{}")

    def load(self, receipt_id: str) -> ReceiptWitnessAttestation:
        attestation = self._current(receipt_id)
        if attestation is None:
            raise ExternalReceiptError("Receipt witness attestation is not registered")
        if self._is_revoked(receipt_id):
            raise ExternalReceiptError("Receipt witness attestation is revoked")
        return attestation

    def verify(
        self,
        receipt: ExternalExecutionReceipt,
        witness: LocalReceiptWitness,
        *,
        issuer_id: str,
    ) -> None:
        attestation = self.load(receipt.receipt_id)
        witness.verify(attestation, receipt, issuer_id=issuer_id)

    def _append(self, event_type: str, receipt_id: str, payload: str) -> None:
        self._connection.execute(
            "INSERT INTO receipt_witness_events(receipt_id, event_type, payload) VALUES (?, ?, ?)",
            (receipt_id, event_type, payload),
        )
        self._connection.commit()

    def _current(self, receipt_id: str) -> ReceiptWitnessAttestation | None:
        rows = self._connection.execute(
            "SELECT event_type, payload FROM receipt_witness_events WHERE receipt_id = ? ORDER BY event_id",
            (receipt_id,),
        ).fetchall()
        current: ReceiptWitnessAttestation | None = None
        for event_type, payload in rows:
            if event_type == "register":
                current = _attestation_from_payload(payload)
        return current

    def _is_revoked(self, receipt_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM receipt_witness_events WHERE receipt_id = ? AND event_type = 'revoke' LIMIT 1",
            (receipt_id,),
        ).fetchone()
        return row is not None


def _attestation_payload(attestation: ReceiptWitnessAttestation) -> str:
    return json.dumps(
        {
            "receipt_id": attestation.receipt_id,
            "issuer_id": attestation.issuer_id,
            "witness_id": attestation.witness_id,
            "receipt_digest": attestation.receipt_digest,
            "signature": attestation.signature,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _attestation_from_payload(payload: str) -> ReceiptWitnessAttestation:
    try:
        value = json.loads(payload)
        return ReceiptWitnessAttestation(
            str(value["receipt_id"]),
            str(value["issuer_id"]),
            str(value["witness_id"]),
            str(value["receipt_digest"]),
            str(value["signature"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ExternalReceiptError("Receipt witness event is malformed") from error


def digest_receipt(receipt: ExternalExecutionReceipt) -> str:
    payload: Mapping[str, object] = {
        "receipt_id": receipt.receipt_id,
        "task_id": receipt.task_id,
        "tool_name": receipt.tool_name,
        "user_id": receipt.user_id,
        "audience": receipt.audience,
        "status": receipt.status,
        "parameters_hash": receipt.parameters_hash,
        "result_hash": receipt.result_hash,
        "issued_at": receipt.issued_at,
        "expires_at": receipt.expires_at,
        "signature": receipt.signature,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
