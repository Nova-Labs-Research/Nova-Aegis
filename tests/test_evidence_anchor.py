from __future__ import annotations

import math
import sqlite3

import pytest

from nova_aegis import (
    AnchoredSQLiteSyntheticEvidenceStore,
    LocalJournalKeyProvider,
    SQLiteSyntheticEvidenceAnchorStore,
    SQLiteSyntheticEvidenceStore,
    SyntheticEvidenceAnchorError,
)


def _open(tmp_path):
    evidence_keys = LocalJournalKeyProvider({"evidence-key": b"evidence-secret"})
    anchor_keys = LocalJournalKeyProvider({"anchor-key": b"anchor-secret"})
    anchor_store = SQLiteSyntheticEvidenceAnchorStore(
        sqlite3.connect(tmp_path / "anchors.db"), anchor_keys
    )
    store = AnchoredSQLiteSyntheticEvidenceStore(
        sqlite3.connect(tmp_path / "evidence.db"),
        evidence_keys,
        store_id="evaluation-store",
        anchor_store=anchor_store,
    )
    return store


def test_anchored_evidence_replays_after_restart(tmp_path) -> None:
    store = _open(tmp_path)
    first = store.append("evidence-1", "transcript", {"valid": True})
    second = store.append("evidence-2", "failure_receipt", {"kind": "timeout"})

    reopened = _open(tmp_path)

    assert reopened.replay() == (first, second)
    record, anchor = reopened.get_verified("evidence-1")
    assert record == first
    assert anchor.event_count == 2
    assert anchor.terminal_digest == second.digest


def test_tail_and_complete_evidence_deletion_are_refused(tmp_path) -> None:
    store = _open(tmp_path)
    store.append("evidence-1", "transcript", {"sequence": 1})
    store.append("evidence-2", "transcript", {"sequence": 2})
    connection = sqlite3.connect(tmp_path / "evidence.db")
    connection.execute("DELETE FROM synthetic_evidence_events WHERE sequence = 2")
    connection.commit()

    with pytest.raises(SyntheticEvidenceAnchorError, match="does not match"):
        store.replay()

    connection.execute("DELETE FROM synthetic_evidence_events")
    connection.commit()
    with pytest.raises(SyntheticEvidenceAnchorError, match="does not match"):
        store.replay()


def test_missing_or_rolled_back_anchor_is_refused(tmp_path) -> None:
    store = _open(tmp_path)
    store.append("evidence-1", "transcript", {"sequence": 1})
    store.append("evidence-2", "transcript", {"sequence": 2})
    anchors = sqlite3.connect(tmp_path / "anchors.db")
    anchors.execute("DELETE FROM synthetic_evidence_anchors WHERE anchor_sequence = 2")
    anchors.commit()

    with pytest.raises(SyntheticEvidenceAnchorError, match="does not match"):
        store.replay()

    anchors.execute("DELETE FROM synthetic_evidence_anchors")
    anchors.commit()
    with pytest.raises(SyntheticEvidenceAnchorError, match="missing"):
        store.replay()


def test_tampered_anchor_signature_blocks_replay_and_append(tmp_path) -> None:
    store = _open(tmp_path)
    store.append("evidence-1", "transcript", {"valid": True})
    anchors = sqlite3.connect(tmp_path / "anchors.db")
    payload = anchors.execute(
        "SELECT payload FROM synthetic_evidence_anchors WHERE anchor_sequence = 1"
    ).fetchone()[0]
    anchors.execute(
        "UPDATE synthetic_evidence_anchors SET payload = ? WHERE anchor_sequence = 1",
        (payload.replace('"signature":"', '"signature":"0'),),
    )
    anchors.commit()

    with pytest.raises(SyntheticEvidenceAnchorError, match="signature"):
        store.replay()
    with pytest.raises(SyntheticEvidenceAnchorError, match="signature"):
        store.append("evidence-2", "transcript", {"valid": True})


def test_unanchored_history_is_refused(tmp_path) -> None:
    evidence_keys = LocalJournalKeyProvider({"evidence-key": b"evidence-secret"})
    SQLiteSyntheticEvidenceStore(
        sqlite3.connect(tmp_path / "evidence.db"), evidence_keys
    ).append("evidence-1", "transcript", {"valid": True})

    with pytest.raises(SyntheticEvidenceAnchorError, match="missing"):
        _open(tmp_path).replay()


def test_non_finite_evidence_payload_is_refused(tmp_path) -> None:
    with pytest.raises(ValueError, match="canonical JSON"):
        _open(tmp_path).append("evidence-1", "transcript", {"score": math.nan})