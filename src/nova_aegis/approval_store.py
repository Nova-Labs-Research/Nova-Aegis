"""Local persistence for synthetic recovery approvals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import hashlib
import hmac
import sqlite3
import threading
from typing import Protocol


@dataclass(frozen=True)
class RecoveryApprovalRecord:
    approval_id: str
    task_id: str
    approver_id: str
    resolution: str
    external_receipt_id: str
    result_hash: str
    issued_at: int
    expires_at: int
    signature: str


@dataclass(frozen=True)
class RecoveryJournalRecord:
    journal_id: str
    task_id: str
    status: str
    result: dict[str, str]
    integrity_hash: str
    key_id: str = "legacy"

    def verify_integrity(self) -> bool:
        payload = json.dumps(
            {
                "journal_id": self.journal_id,
                "task_id": self.task_id,
                "status": self.status,
                "result": self.result,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        expected = hashlib.sha256(payload).hexdigest()
        return hmac.compare_digest(self.integrity_hash, expected)


def recovery_journal_hash(
    journal_id: str,
    task_id: str,
    status: str,
    result: dict[str, str],
    secret: bytes | None = None,
) -> str:
    payload = json.dumps(
        {
            "journal_id": journal_id,
            "task_id": task_id,
            "status": status,
            "result": result,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if secret is not None:
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return hashlib.sha256(payload).hexdigest()


class ApprovalStore(Protocol):
    def create(self, approval: RecoveryApprovalRecord) -> None: ...

    def get(self, approval_id: str) -> RecoveryApprovalRecord | None: ...

    def consume(self, approval_id: str, *, now: int) -> bool: ...

    def revoke(self, approval_id: str, *, now: int) -> bool: ...

    def begin_recovery(
        self,
        approval_id: str,
        *,
        task_id: str,
        status: str,
        result: dict[str, str],
        now: int,
    ) -> bool: ...

    def pending_recoveries(self) -> tuple[RecoveryJournalRecord, ...]: ...

    def complete_recovery(self, journal_id: str) -> bool: ...

    def close(self) -> None: ...


class InMemoryApprovalStore:
    """Process-local approval persistence for the synthetic gateway."""

    def __init__(self) -> None:
        self._records: dict[str, RecoveryApprovalRecord] = {}
        self._journals: dict[str, RecoveryJournalRecord] = {}

    def create(self, approval: RecoveryApprovalRecord) -> None:
        if approval.approval_id in self._records:
            raise ValueError("MCP recovery approval already exists")
        self._records[approval.approval_id] = approval

    def get(self, approval_id: str) -> RecoveryApprovalRecord | None:
        return self._records.get(approval_id)

    def consume(self, approval_id: str, *, now: int) -> bool:
        approval = self._records.get(approval_id)
        if approval is None or approval.expires_at <= now:
            return False
        del self._records[approval_id]
        return True

    def revoke(self, approval_id: str, *, now: int) -> bool:
        return self._records.pop(approval_id, None) is not None

    def begin_recovery(
        self,
        approval_id: str,
        *,
        task_id: str,
        status: str,
        result: dict[str, str],
        now: int,
    ) -> bool:
        if not self.consume(approval_id, now=now):
            return False
        self._journals[approval_id] = RecoveryJournalRecord(
            approval_id,
            task_id,
            status,
            dict(result),
            recovery_journal_hash(approval_id, task_id, status, result),
        )
        return True

    def pending_recoveries(self) -> tuple[RecoveryJournalRecord, ...]:
        return tuple(self._journals.values())

    def complete_recovery(self, journal_id: str) -> bool:
        return self._journals.pop(journal_id, None) is not None

    def close(self) -> None:
        return None


class SQLiteApprovalStore:
    """Durable local approval persistence with atomic single-use consumption."""

    def __init__(self, database: str) -> None:
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._lock = threading.RLock()
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mcp_recovery_approvals (
                approval_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                approver_id TEXT NOT NULL,
                resolution TEXT NOT NULL,
                external_receipt_id TEXT NOT NULL,
                result_hash TEXT NOT NULL,
                issued_at INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                signature TEXT NOT NULL,
                consumed_at TEXT,
                revoked_at TEXT
            )
            """
        )
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mcp_recovery_journal (
                journal_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT NOT NULL,
                integrity_hash TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        columns = {
            row[1]
            for row in self._connection.execute("PRAGMA table_info(mcp_recovery_journal)")
        }
        if "integrity_hash" not in columns:
            self._connection.execute(
                "ALTER TABLE mcp_recovery_journal ADD COLUMN integrity_hash TEXT"
            )
        columns = {row[1] for row in self._connection.execute("PRAGMA table_info(mcp_recovery_approvals)")}
        if "revoked_at" not in columns:
            self._connection.execute(
                "ALTER TABLE mcp_recovery_approvals ADD COLUMN revoked_at TEXT"
            )
        self._connection.commit()

    def create(self, approval: RecoveryApprovalRecord) -> None:
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO mcp_recovery_approvals
                (approval_id, task_id, approver_id, resolution, external_receipt_id,
                 result_hash, issued_at, expires_at, signature, consumed_at, revoked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    approval.approval_id,
                    approval.task_id,
                    approval.approver_id,
                    approval.resolution,
                    approval.external_receipt_id,
                    approval.result_hash,
                    approval.issued_at,
                    approval.expires_at,
                    approval.signature,
                ),
            )
            self._connection.commit()

    def get(self, approval_id: str) -> RecoveryApprovalRecord | None:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT approval_id, task_id, approver_id, resolution, external_receipt_id,
                       result_hash, issued_at, expires_at, signature
                FROM mcp_recovery_approvals
                WHERE approval_id = ? AND consumed_at IS NULL AND revoked_at IS NULL
                """,
                (approval_id,),
            ).fetchone()
        if row is None:
            return None
        return RecoveryApprovalRecord(*row)

    def consume(self, approval_id: str, *, now: int) -> bool:
        with self._lock:
            cursor = self._connection.execute(
                """
                UPDATE mcp_recovery_approvals
                SET consumed_at = ?
                WHERE approval_id = ? AND consumed_at IS NULL AND revoked_at IS NULL AND expires_at > ?
                """,
                (datetime.now(timezone.utc).isoformat(), approval_id, now),
            )
            self._connection.commit()
        return cursor.rowcount == 1

    def revoke(self, approval_id: str, *, now: int) -> bool:
        with self._lock:
            cursor = self._connection.execute(
                """
                UPDATE mcp_recovery_approvals
                SET revoked_at = ?
                WHERE approval_id = ? AND consumed_at IS NULL AND revoked_at IS NULL
                """,
                (datetime.now(timezone.utc).isoformat(), approval_id),
            )
            self._connection.commit()
        return cursor.rowcount == 1

    def begin_recovery(
        self,
        approval_id: str,
        *,
        task_id: str,
        status: str,
        result: dict[str, str],
        now: int,
    ) -> bool:
        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                cursor = self._connection.execute(
                    """
                    UPDATE mcp_recovery_approvals
                    SET consumed_at = ?
                    WHERE approval_id = ? AND consumed_at IS NULL
                      AND revoked_at IS NULL AND expires_at > ?
                    """,
                    (datetime.now(timezone.utc).isoformat(), approval_id, now),
                )
                if cursor.rowcount != 1:
                    self._connection.rollback()
                    return False
                self._connection.execute(
                    """
                    INSERT INTO mcp_recovery_journal
                    (journal_id, task_id, status, result_json, integrity_hash, completed_at)
                    VALUES (?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        approval_id,
                        task_id,
                        status,
                        json.dumps(result, sort_keys=True, separators=(",", ":")),
                        recovery_journal_hash(approval_id, task_id, status, result),
                    ),
                )
                self._connection.commit()
                return True
            except Exception:
                self._connection.rollback()
                raise

    def pending_recoveries(self) -> tuple[RecoveryJournalRecord, ...]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT journal_id, task_id, status, result_json, integrity_hash
                FROM mcp_recovery_journal
                WHERE completed_at IS NULL
                ORDER BY journal_id
                """
            ).fetchall()
        return tuple(
            RecoveryJournalRecord(row[0], row[1], row[2], json.loads(row[3]), row[4] or "")
            for row in rows
        )

    def complete_recovery(self, journal_id: str) -> bool:
        with self._lock:
            cursor = self._connection.execute(
                """
                UPDATE mcp_recovery_journal
                SET completed_at = ?
                WHERE journal_id = ? AND completed_at IS NULL
                """,
                (datetime.now(timezone.utc).isoformat(), journal_id),
            )
            self._connection.commit()
        return cursor.rowcount == 1

    def close(self) -> None:
        with self._lock:
            self._connection.close()
