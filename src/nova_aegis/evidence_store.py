"""Authenticated append-only storage for synthetic evaluation evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import sqlite3
from typing import Any, Mapping, Protocol


class SyntheticEvidenceKeyProvider(Protocol):
    def get(self, key_id: str) -> bytes | None: ...

    def active(self) -> tuple[str, bytes] | None: ...


class SyntheticEvidenceError(RuntimeError):
    """Raised when synthetic evidence cannot be trusted or persisted."""


@dataclass(frozen=True)
class SyntheticEvidenceRecord:
    sequence: int
    evidence_id: str
    evidence_type: str
    payload_json: str
    previous_digest: str
    key_id: str
    digest: str
    signature: str

    def payload(self) -> dict[str, Any]:
        value = json.loads(self.payload_json)
        if not isinstance(value, dict):
            raise SyntheticEvidenceError("Synthetic evidence payload is malformed")
        return value


class SQLiteSyntheticEvidenceStore:
    """Local authenticated event chain; this is not protected key custody."""

    EVIDENCE_TYPES = frozenset({"transcript", "failure_receipt"})

    def __init__(
        self,
        connection: sqlite3.Connection,
        key_provider: SyntheticEvidenceKeyProvider,
    ) -> None:
        self._connection = connection
        self._key_provider = key_provider
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_evidence_events (
                sequence INTEGER PRIMARY KEY,
                evidence_id TEXT NOT NULL UNIQUE,
                evidence_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                previous_digest TEXT NOT NULL,
                key_id TEXT NOT NULL,
                digest TEXT NOT NULL,
                signature TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def append(
        self,
        evidence_id: str,
        evidence_type: str,
        payload: Mapping[str, Any],
    ) -> SyntheticEvidenceRecord:
        if not evidence_id.strip():
            raise ValueError("Synthetic evidence ID is required")
        if evidence_type not in self.EVIDENCE_TYPES:
            raise ValueError("Synthetic evidence type is invalid")
        history = self.replay()
        if any(record.evidence_id == evidence_id for record in history):
            raise SyntheticEvidenceError("Synthetic evidence ID already exists")
        active = self._key_provider.active()
        if active is None:
            raise SyntheticEvidenceError("Synthetic evidence requires an active signing key")
        key_id, secret = active
        sequence = len(history) + 1
        previous_digest = history[-1].digest if history else ""
        payload_json = _canonical_payload(payload)
        digest = _digest(sequence, evidence_id, evidence_type, payload_json, previous_digest, key_id)
        signature = hmac.new(secret, digest.encode("ascii"), hashlib.sha256).hexdigest()
        record = SyntheticEvidenceRecord(
            sequence,
            evidence_id,
            evidence_type,
            payload_json,
            previous_digest,
            key_id,
            digest,
            signature,
        )
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO synthetic_evidence_events(
                        sequence, evidence_id, evidence_type, payload_json,
                        previous_digest, key_id, digest, signature
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.sequence,
                        record.evidence_id,
                        record.evidence_type,
                        record.payload_json,
                        record.previous_digest,
                        record.key_id,
                        record.digest,
                        record.signature,
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise SyntheticEvidenceError("Synthetic evidence conflicts with existing history") from error
        return record

    def replay(self) -> tuple[SyntheticEvidenceRecord, ...]:
        rows = self._connection.execute(
            """
            SELECT sequence, evidence_id, evidence_type, payload_json,
                   previous_digest, key_id, digest, signature
            FROM synthetic_evidence_events ORDER BY sequence
            """
        ).fetchall()
        records: list[SyntheticEvidenceRecord] = []
        evidence_ids: set[str] = set()
        previous_digest = ""
        for expected_sequence, row in enumerate(rows, start=1):
            record = SyntheticEvidenceRecord(*row)
            if record.sequence != expected_sequence or record.evidence_id in evidence_ids:
                raise SyntheticEvidenceError("Synthetic evidence sequence is corrupt")
            if record.evidence_type not in self.EVIDENCE_TYPES:
                raise SyntheticEvidenceError("Synthetic evidence type is corrupt")
            try:
                canonical_payload = _canonical_payload(record.payload())
            except (json.JSONDecodeError, TypeError, ValueError) as error:
                raise SyntheticEvidenceError("Synthetic evidence payload is malformed") from error
            if canonical_payload != record.payload_json or record.previous_digest != previous_digest:
                raise SyntheticEvidenceError("Synthetic evidence chain is corrupt")
            expected_digest = _digest(
                record.sequence,
                record.evidence_id,
                record.evidence_type,
                record.payload_json,
                record.previous_digest,
                record.key_id,
            )
            secret = self._key_provider.get(record.key_id)
            if secret is None:
                raise SyntheticEvidenceError("Synthetic evidence signing key is not trusted")
            expected_signature = hmac.new(
                secret, expected_digest.encode("ascii"), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(record.digest, expected_digest) or not hmac.compare_digest(
                record.signature, expected_signature
            ):
                raise SyntheticEvidenceError("Synthetic evidence authentication failed")
            records.append(record)
            evidence_ids.add(record.evidence_id)
            previous_digest = record.digest
        return tuple(records)


def _canonical_payload(payload: Mapping[str, Any]) -> str:
    try:
        return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as error:
        raise ValueError("Synthetic evidence payload must be canonical JSON") from error


def _digest(
    sequence: int,
    evidence_id: str,
    evidence_type: str,
    payload_json: str,
    previous_digest: str,
    key_id: str,
) -> str:
    value = {
        "sequence": sequence,
        "evidence_id": evidence_id,
        "evidence_type": evidence_type,
        "payload_json": payload_json,
        "previous_digest": previous_digest,
        "key_id": key_id,
    }
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()