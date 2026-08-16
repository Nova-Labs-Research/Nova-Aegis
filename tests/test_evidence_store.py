from __future__ import annotations

import sqlite3

import pytest

from nova_aegis import (
    LocalJournalKeyProvider,
    SQLiteSyntheticEvidenceStore,
    SyntheticEvidenceError,
)


def _keys() -> LocalJournalKeyProvider:
    return LocalJournalKeyProvider({"evidence-key": b"synthetic-secret"})


def test_evidence_replays_after_restart_with_authenticated_chain(tmp_path) -> None:
    database = tmp_path / "evidence.db"
    connection = sqlite3.connect(database)
    store = SQLiteSyntheticEvidenceStore(connection, _keys())
    first = store.append("transcript-1", "transcript", {"events": ["goal_signal"]})
    second = store.append("failure-1", "failure_receipt", {"kind": "timeout"})
    connection.close()

    replayed = SQLiteSyntheticEvidenceStore(sqlite3.connect(database), _keys()).replay()

    assert replayed == (first, second)
    assert replayed[1].previous_digest == replayed[0].digest
    assert replayed[0].payload() == {"events": ["goal_signal"]}


def test_payload_tampering_is_refused_after_restart(tmp_path) -> None:
    database = tmp_path / "evidence.db"
    connection = sqlite3.connect(database)
    store = SQLiteSyntheticEvidenceStore(connection, _keys())
    store.append("transcript-1", "transcript", {"valid": True})
    connection.execute(
        "UPDATE synthetic_evidence_events SET payload_json = ? WHERE evidence_id = ?",
        ('{"valid":false}', "transcript-1"),
    )
    connection.commit()
    connection.close()

    reopened = SQLiteSyntheticEvidenceStore(sqlite3.connect(database), _keys())
    with pytest.raises(SyntheticEvidenceError, match="authentication"):
        reopened.replay()


def test_missing_middle_event_is_refused(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "evidence.db")
    store = SQLiteSyntheticEvidenceStore(connection, _keys())
    for sequence in range(1, 4):
        store.append(f"evidence-{sequence}", "transcript", {"sequence": sequence})
    connection.execute("DELETE FROM synthetic_evidence_events WHERE sequence = 2")
    connection.commit()

    with pytest.raises(SyntheticEvidenceError, match="sequence"):
        store.replay()


def test_unknown_historical_key_is_refused(tmp_path) -> None:
    database = tmp_path / "evidence.db"
    connection = sqlite3.connect(database)
    SQLiteSyntheticEvidenceStore(connection, _keys()).append(
        "transcript-1", "transcript", {"valid": True}
    )
    connection.close()

    reopened = SQLiteSyntheticEvidenceStore(
        sqlite3.connect(database), LocalJournalKeyProvider()
    )
    with pytest.raises(SyntheticEvidenceError, match="not trusted"):
        reopened.replay()


def test_corrupt_history_blocks_further_append(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "evidence.db")
    store = SQLiteSyntheticEvidenceStore(connection, _keys())
    store.append("transcript-1", "transcript", {"valid": True})
    connection.execute(
        "UPDATE synthetic_evidence_events SET previous_digest = 'tampered' WHERE sequence = 1"
    )
    connection.commit()

    with pytest.raises(SyntheticEvidenceError, match="chain"):
        store.append("transcript-2", "transcript", {"valid": True})


def test_duplicate_invalid_and_partial_evidence_fail_closed(tmp_path) -> None:
    connection = sqlite3.connect(tmp_path / "evidence.db")
    store = SQLiteSyntheticEvidenceStore(connection, _keys())
    store.append("transcript-1", "transcript", {"valid": True})
    with pytest.raises(SyntheticEvidenceError, match="already exists"):
        store.append("transcript-1", "transcript", {"valid": True})
    with pytest.raises(ValueError, match="type"):
        store.append("unknown-1", "unknown", {})
    connection.execute(
        """
        INSERT INTO synthetic_evidence_events VALUES
        (2, 'partial-1', 'transcript', '{}', '', 'evidence-key', '', '')
        """
    )
    connection.commit()
    with pytest.raises(SyntheticEvidenceError):
        store.replay()