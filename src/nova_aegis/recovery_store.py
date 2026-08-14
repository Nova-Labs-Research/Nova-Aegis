"""Unified local SQLite persistence for synthetic recovery bookkeeping."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import hmac
import sqlite3
import threading
from typing import Mapping

from .approval_store import (
    RecoveryApprovalRecord,
    RecoveryJournalRecord,
    recovery_journal_hash,
)
from .task_store import SQLiteTaskStore, TaskRecord
from .key_provider import JournalKeyProvider, LocalJournalKeyProvider


class SQLiteRecoveryStore(SQLiteTaskStore):
    """Task and recovery approval state sharing one local SQLite transaction."""

    def __init__(
        self,
        database: str,
        *,
        journal_secret: bytes | None = None,
        journal_keys: Mapping[str, bytes] | None = None,
        active_journal_key_id: str | None = None,
        key_provider: JournalKeyProvider | None = None,
    ) -> None:
        super().__init__(database)
        self._approval_lock = threading.RLock()
        if key_provider is not None and (journal_secret is not None or journal_keys is not None):
            raise ValueError("Provide key_provider or raw journal keys, not both")
        if journal_keys is not None and journal_secret is not None:
            raise ValueError("Provide journal_keys or journal_secret, not both")
        self._key_provider = key_provider or LocalJournalKeyProvider(
            dict(journal_keys or {})
            | ({"journal-v1": journal_secret} if journal_secret is not None else {}),
            active_key_id=active_journal_key_id,
        )
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
                key_id TEXT NOT NULL DEFAULT 'legacy',
                completed_at TEXT
            )
            """
        )
        columns = {
            row[1]
            for row in self._connection.execute("PRAGMA table_info(mcp_recovery_journal)")
        }
        if "key_id" not in columns:
            self._connection.execute(
                "ALTER TABLE mcp_recovery_journal ADD COLUMN key_id TEXT NOT NULL DEFAULT 'legacy'"
            )
        self._connection.commit()

    def create(self, record: TaskRecord | RecoveryApprovalRecord) -> None:
        if isinstance(record, RecoveryApprovalRecord):
            with self._approval_lock:
                self._connection.execute(
                    """
                    INSERT INTO mcp_recovery_approvals
                    (approval_id, task_id, approver_id, resolution, external_receipt_id,
                     result_hash, issued_at, expires_at, signature, consumed_at, revoked_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                    """,
                    (
                        record.approval_id,
                        record.task_id,
                        record.approver_id,
                        record.resolution,
                        record.external_receipt_id,
                        record.result_hash,
                        record.issued_at,
                        record.expires_at,
                        record.signature,
                    ),
                )
                self._connection.commit()
            return
        super().create(record)

    def get(self, record_id: str) -> TaskRecord | RecoveryApprovalRecord | None:
        task = super().get(record_id)
        if task is not None:
            return task
        with self._approval_lock:
            row = self._connection.execute(
                """
                SELECT approval_id, task_id, approver_id, resolution, external_receipt_id,
                       result_hash, issued_at, expires_at, signature
                FROM mcp_recovery_approvals
                WHERE approval_id = ? AND consumed_at IS NULL AND revoked_at IS NULL
                """,
                (record_id,),
            ).fetchone()
        return RecoveryApprovalRecord(*row) if row is not None else None

    def consume(self, approval_id: str, *, now: int) -> bool:
        with self._approval_lock:
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
        with self._approval_lock:
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
        with self._approval_lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                if not self._consume_without_commit(approval_id, now):
                    self._connection.rollback()
                    return False
                self._insert_journal(approval_id, task_id, status, result)
                self._connection.commit()
                return True
            except Exception:
                self._connection.rollback()
                raise

    def finalize_recovery(
        self,
        approval_id: str,
        *,
        task_id: str,
        status: str,
        result: dict[str, str],
        now: int,
    ) -> bool:
        with self._approval_lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                if not self._consume_without_commit(approval_id, now):
                    self._connection.rollback()
                    return False
                self._insert_journal(approval_id, task_id, status, result)
                cursor = self._connection.execute(
                    """
                    UPDATE mcp_tasks
                    SET status = ?, result_json = ?, lease_owner = NULL,
                        lease_expires_at = NULL, updated_at = ?
                    WHERE task_id = ? AND status = 'recovery_required'
                    """,
                    (
                        status,
                        json.dumps(result, sort_keys=True, separators=(",", ":")),
                        datetime.now(timezone.utc).isoformat(),
                        task_id,
                    ),
                )
                if cursor.rowcount != 1:
                    self._connection.rollback()
                    return False
                self._connection.execute(
                    """
                    UPDATE mcp_recovery_journal
                    SET completed_at = ?
                    WHERE journal_id = ? AND completed_at IS NULL
                    """,
                    (datetime.now(timezone.utc).isoformat(), approval_id),
                )
                self._connection.commit()
                return True
            except Exception:
                self._connection.rollback()
                raise

    def pending_recoveries(self) -> tuple[RecoveryJournalRecord, ...]:
        with self._approval_lock:
            rows = self._connection.execute(
                """
                SELECT journal_id, task_id, status, result_json, integrity_hash, key_id
                FROM mcp_recovery_journal
                WHERE completed_at IS NULL
                ORDER BY journal_id
                """
            ).fetchall()
        return tuple(
            RecoveryJournalRecord(
                row[0], row[1], row[2], json.loads(row[3]), row[4] or "", row[5] or "legacy"
            )
            for row in rows
        )

    def verify_journal(self, journal: RecoveryJournalRecord) -> bool:
        if journal.key_id == "legacy":
            return journal.verify_integrity()
        secret = self._key_provider.get(journal.key_id)
        if secret is None:
            return False
        expected = recovery_journal_hash(
            journal.journal_id,
            journal.task_id,
            journal.status,
            journal.result,
            secret,
        )
        return hmac.compare_digest(journal.integrity_hash, expected)

    def rotate_journal_key(self, key_id: str, secret: bytes, *, authority: str = "synthetic-key-admin") -> None:
        with self._approval_lock:
            self._key_provider.rotate(key_id, secret, authority=authority)

    def retire_journal_key(self, key_id: str, *, authority: str = "synthetic-key-admin") -> None:
        with self._approval_lock:
            self._key_provider.retire(key_id, authority=authority)

    def complete_recovery(self, journal_id: str) -> bool:
        with self._approval_lock:
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

    def _consume_without_commit(self, approval_id: str, now: int) -> bool:
        cursor = self._connection.execute(
            """
            UPDATE mcp_recovery_approvals
            SET consumed_at = ?
            WHERE approval_id = ? AND consumed_at IS NULL AND revoked_at IS NULL AND expires_at > ?
            """,
            (datetime.now(timezone.utc).isoformat(), approval_id, now),
        )
        return cursor.rowcount == 1

    def _insert_journal(
        self,
        journal_id: str,
        task_id: str,
        status: str,
        result: dict[str, str],
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO mcp_recovery_journal
            (journal_id, task_id, status, result_json, integrity_hash, key_id, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (
                journal_id,
                task_id,
                status,
                json.dumps(result, sort_keys=True, separators=(",", ":")),
                recovery_journal_hash(journal_id, task_id, status, result, active[1])
                if (active := self._key_provider.active()) is not None
                else recovery_journal_hash(journal_id, task_id, status, result),
                active[0] if active is not None else "legacy",
            ),
        )
