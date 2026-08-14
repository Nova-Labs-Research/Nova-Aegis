from __future__ import annotations

import sqlite3

import pytest

from nova_aegis import (
    BoundaryDecisionError,
    BoundaryPreflightReport,
    SignedBoundaryDecision,
    SQLiteBoundaryDecisionStore,
)


class StaticDecisionKeys:
    def __init__(self, keys: dict[str, bytes], active_key: str | None) -> None:
        self._keys = keys
        self._active_key = active_key

    def get(self, key_id: str) -> bytes | None:
        return self._keys.get(key_id)

    def active(self) -> tuple[str, bytes] | None:
        if self._active_key is None:
            return None
        return self._active_key, self._keys[self._active_key]


def _decision() -> tuple[BoundaryPreflightReport, SignedBoundaryDecision, StaticDecisionKeys]:
    report = BoundaryPreflightReport("local-witness", "CONTINUE_SYNTHETIC", (), False)
    keys = StaticDecisionKeys({"decision-1": b"decision-secret"}, "decision-1")
    return report, SignedBoundaryDecision.from_report(report, keys), keys


def test_decision_store_replays_after_sqlite_close_and_reopen(tmp_path) -> None:
    report, decision, keys = _decision()
    database_path = tmp_path / "boundary-decisions.sqlite3"
    connection = sqlite3.connect(database_path)
    store = SQLiteBoundaryDecisionStore(connection)
    store.register(decision)
    connection.close()

    connection = sqlite3.connect(database_path)
    store = SQLiteBoundaryDecisionStore(connection)
    assert store.replay("local-witness", report, keys) == decision


def test_decision_store_rejects_conflict_and_revocation(tmp_path) -> None:
    report, decision, keys = _decision()
    connection = sqlite3.connect(tmp_path / "boundary-decisions.sqlite3")
    store = SQLiteBoundaryDecisionStore(connection)
    store.register(decision)

    conflicting = SignedBoundaryDecision(
        decision.boundary,
        "REFACTOR",
        ("forged",),
        False,
        decision.key_id,
        decision.signature,
    )
    with pytest.raises(BoundaryDecisionError, match="conflicting"):
        store.register(conflicting)

    store.revoke("local-witness")
    with pytest.raises(BoundaryDecisionError, match="revoked"):
        store.replay("local-witness", report, keys)


def test_decision_store_rejects_unknown_key_and_malformed_event(tmp_path) -> None:
    report, decision, keys = _decision()
    connection = sqlite3.connect(tmp_path / "boundary-decisions.sqlite3")
    store = SQLiteBoundaryDecisionStore(connection)
    store.register(decision)

    unknown_keys = StaticDecisionKeys({"other": b"other-secret"}, "other")
    with pytest.raises(BoundaryDecisionError, match="trusted"):
        store.replay("local-witness", report, unknown_keys)

    connection.execute(
        "INSERT INTO boundary_decision_events(boundary, event_type, payload) VALUES (?, ?, ?)",
        ("malformed", "register", "not-json"),
    )
    connection.commit()
    with pytest.raises(BoundaryDecisionError, match="malformed"):
        store.replay("malformed", report, keys)
