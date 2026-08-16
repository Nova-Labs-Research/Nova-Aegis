"""Separately persisted signed checkpoints for synthetic evidence histories."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import sqlite3
from typing import Any, Mapping

from .evidence_store import (
    SQLiteSyntheticEvidenceStore,
    SyntheticEvidenceError,
    SyntheticEvidenceKeyProvider,
    SyntheticEvidenceRecord,
)


class SyntheticEvidenceAnchorError(SyntheticEvidenceError):
    """Raised when an evidence checkpoint cannot be trusted."""


@dataclass(frozen=True)
class SignedSyntheticEvidenceAnchor:
    store_id: str
    event_count: int
    terminal_digest: str
    previous_anchor_digest: str
    key_id: str
    signature: str

    def payload(self) -> dict[str, Any]:
        return {
            "store_id": self.store_id,
            "event_count": self.event_count,
            "terminal_digest": self.terminal_digest,
            "previous_anchor_digest": self.previous_anchor_digest,
            "key_id": self.key_id,
        }

    def digest(self) -> str:
        return hashlib.sha256(_canonical({**self.payload(), "signature": self.signature})).hexdigest()


class SQLiteSyntheticEvidenceAnchorStore:
    """Separate signed checkpoint history; use independently retained storage."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        key_provider: SyntheticEvidenceKeyProvider,
    ) -> None:
        self._connection = connection
        self._key_provider = key_provider
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS synthetic_evidence_anchors (
                anchor_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id TEXT NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def advance(
        self,
        store_id: str,
        event_count: int,
        terminal_digest: str,
    ) -> SignedSyntheticEvidenceAnchor:
        if not store_id.strip() or event_count <= 0 or not terminal_digest.strip():
            raise ValueError("Synthetic evidence anchor fields are invalid")
        history = self._history(store_id)
        if event_count != len(history) + 1:
            raise SyntheticEvidenceAnchorError("Synthetic evidence anchor sequence is invalid")
        active = self._key_provider.active()
        if active is None:
            raise SyntheticEvidenceAnchorError("Synthetic evidence anchor requires an active key")
        key_id, secret = active
        unsigned = SignedSyntheticEvidenceAnchor(
            store_id,
            event_count,
            terminal_digest,
            history[-1].digest() if history else "",
            key_id,
            "",
        )
        anchor = SignedSyntheticEvidenceAnchor(
            **unsigned.payload(),
            signature=hmac.new(secret, _canonical(unsigned.payload()), hashlib.sha256).hexdigest(),
        )
        with self._connection:
            self._connection.execute(
                "INSERT INTO synthetic_evidence_anchors(store_id, payload) VALUES (?, ?)",
                (store_id, _anchor_payload(anchor)),
            )
        return anchor

    def verify_current(
        self,
        store_id: str,
        event_count: int,
        terminal_digest: str,
    ) -> SignedSyntheticEvidenceAnchor | None:
        history = self._history(store_id)
        if not history:
            if event_count == 0 and terminal_digest == "":
                return None
            raise SyntheticEvidenceAnchorError("Synthetic evidence anchor is missing")
        anchor = history[-1]
        if anchor.event_count != event_count or anchor.terminal_digest != terminal_digest:
            raise SyntheticEvidenceAnchorError("Synthetic evidence does not match its anchor")
        return anchor

    def _history(self, store_id: str) -> tuple[SignedSyntheticEvidenceAnchor, ...]:
        rows = self._connection.execute(
            """
            SELECT payload FROM synthetic_evidence_anchors
            WHERE store_id = ? ORDER BY anchor_sequence
            """,
            (store_id,),
        ).fetchall()
        anchors: list[SignedSyntheticEvidenceAnchor] = []
        for expected_count, (payload,) in enumerate(rows, start=1):
            anchor = _anchor_from_payload(payload)
            if anchor.store_id != store_id or anchor.event_count != expected_count:
                raise SyntheticEvidenceAnchorError("Synthetic evidence anchor history is corrupt")
            previous_digest = anchors[-1].digest() if anchors else ""
            if anchor.previous_anchor_digest != previous_digest:
                raise SyntheticEvidenceAnchorError("Synthetic evidence anchor chain is corrupt")
            secret = self._key_provider.get(anchor.key_id)
            if secret is None:
                raise SyntheticEvidenceAnchorError("Synthetic evidence anchor key is not trusted")
            expected_signature = hmac.new(
                secret, _canonical(anchor.payload()), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(anchor.signature, expected_signature):
                raise SyntheticEvidenceAnchorError("Synthetic evidence anchor signature is invalid")
            anchors.append(anchor)
        return tuple(anchors)


class AnchoredSQLiteSyntheticEvidenceStore:
    """Evidence store that refuses replay unless a separate checkpoint agrees."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        evidence_key_provider: SyntheticEvidenceKeyProvider,
        *,
        store_id: str,
        anchor_store: SQLiteSyntheticEvidenceAnchorStore,
    ) -> None:
        if not store_id.strip():
            raise ValueError("Synthetic evidence store identity is required")
        self.store_id = store_id
        self._store = SQLiteSyntheticEvidenceStore(connection, evidence_key_provider)
        self._anchor_store = anchor_store

    def append(
        self,
        evidence_id: str,
        evidence_type: str,
        payload: Mapping[str, Any],
    ) -> SyntheticEvidenceRecord:
        self.replay()
        record = self._store.append(evidence_id, evidence_type, payload)
        self._anchor_store.advance(self.store_id, record.sequence, record.digest)
        return record

    def replay(self) -> tuple[SyntheticEvidenceRecord, ...]:
        records = self._store.replay()
        terminal_digest = records[-1].digest if records else ""
        self._anchor_store.verify_current(self.store_id, len(records), terminal_digest)
        return records

    def get_verified(
        self,
        evidence_id: str,
    ) -> tuple[SyntheticEvidenceRecord, SignedSyntheticEvidenceAnchor]:
        records = self.replay()
        record = next((item for item in records if item.evidence_id == evidence_id), None)
        if record is None:
            raise SyntheticEvidenceAnchorError("Anchored synthetic evidence is missing")
        anchor = self._anchor_store.verify_current(
            self.store_id,
            len(records),
            records[-1].digest,
        )
        if anchor is None:
            raise SyntheticEvidenceAnchorError("Synthetic evidence anchor is missing")
        return record, anchor


def _canonical(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("Synthetic evidence anchor must be canonical JSON") from error


def _anchor_payload(anchor: SignedSyntheticEvidenceAnchor) -> str:
    return _canonical({**anchor.payload(), "signature": anchor.signature}).decode("utf-8")


def _anchor_from_payload(payload: str) -> SignedSyntheticEvidenceAnchor:
    try:
        value = json.loads(payload)
        return SignedSyntheticEvidenceAnchor(
            store_id=str(value["store_id"]),
            event_count=int(value["event_count"]),
            terminal_digest=str(value["terminal_digest"]),
            previous_anchor_digest=str(value["previous_anchor_digest"]),
            key_id=str(value["key_id"]),
            signature=str(value["signature"]),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise SyntheticEvidenceAnchorError("Synthetic evidence anchor is malformed") from error