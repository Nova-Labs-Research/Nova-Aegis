from __future__ import annotations

import sqlite3

import pytest

from nova_aegis import AuditIntegrityError, SQLiteAuditLog


def test_sqlite_audit_log_persists_events_and_verifies_chain(tmp_path) -> None:
    database = str(tmp_path / "audit.db")
    audit_log = SQLiteAuditLog(database)
    audit_log.append("request_received", request_id="req-1", question="status?")
    audit_log.append("response_blocked", request_id="req-1", reason="no evidence")
    audit_log.close()

    reopened = SQLiteAuditLog(database)
    events = reopened.events

    assert [event["event_type"] for event in events] == [
        "request_received",
        "response_blocked",
    ]
    assert events[0]["request_id"] == "req-1"
    assert events[0]["event_hash"]
    reopened.verify_integrity()
    reopened.close()


def test_sqlite_audit_log_detects_tampering_and_refuses_append(tmp_path) -> None:
    database = str(tmp_path / "audit.db")
    audit_log = SQLiteAuditLog(database)
    audit_log.append("request_received", request_id="req-1")

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE audit_events SET details_json = ? WHERE sequence = 1",
            ('{"request_id":"forged"}',),
        )
        connection.commit()

    with pytest.raises(AuditIntegrityError, match="integrity"):
        audit_log.verify_integrity()
    with pytest.raises(AuditIntegrityError, match="integrity"):
        audit_log.append("response_blocked", request_id="req-1")
    audit_log.close()


def test_sqlite_audit_log_rejects_unknown_event_types(tmp_path) -> None:
    audit_log = SQLiteAuditLog(str(tmp_path / "audit.db"))

    with pytest.raises(ValueError, match="Unsupported audit event"):
        audit_log.append("unknown_event")

    audit_log.close()


def test_sqlite_audit_log_rejects_reserved_detail_fields(tmp_path) -> None:
    audit_log = SQLiteAuditLog(str(tmp_path / "audit.db"))

    with pytest.raises(ValueError, match="reserved event fields"):
        audit_log.append("request_received", event_id="forged")

    audit_log.close()
