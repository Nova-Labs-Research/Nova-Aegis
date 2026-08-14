"""Local task-state persistence for the synthetic MCP gateway."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from typing import Protocol


@dataclass(frozen=True)
class TaskRecord:
    task_id: str
    user_id: str
    expires_at: int
    status: str
    result: dict[str, str] | None = None
    lease_owner: str | None = None
    lease_expires_at: int | None = None
    fencing_token: int | None = None


class TaskStore(Protocol):
    def create(self, record: TaskRecord) -> None: ...

    def get(self, task_id: str) -> TaskRecord | None: ...

    def update(self, task_id: str, *, status: str, result: dict[str, str] | None = None) -> None: ...

    def claim(self, task_id: str, *, worker_id: str, lease_expires_at: int) -> int | None: ...

    def renew(
        self,
        task_id: str,
        *,
        worker_id: str,
        fencing_token: int,
        lease_expires_at: int,
        now: int,
    ) -> bool: ...

    def finish(
        self,
        task_id: str,
        *,
        worker_id: str,
        fencing_token: int,
        status: str,
        result: dict[str, str] | None = None,
        now: int,
    ) -> bool: ...

    def count_active(self, user_id: str) -> int: ...

    def expire(self, now: int) -> None: ...

    def close(self) -> None: ...


class InMemoryTaskStore:
    """Process-local task state for the default synthetic gateway."""

    def __init__(self) -> None:
        self._records: dict[str, TaskRecord] = {}

    def create(self, record: TaskRecord) -> None:
        if record.task_id in self._records:
            raise ValueError("MCP task already exists")
        self._records[record.task_id] = record

    def get(self, task_id: str) -> TaskRecord | None:
        return self._records.get(task_id)

    def update(self, task_id: str, *, status: str, result: dict[str, str] | None = None) -> None:
        record = self._records.get(task_id)
        if record is None:
            raise ValueError("MCP task does not exist")
        self._records[task_id] = TaskRecord(
            task_id=record.task_id,
            user_id=record.user_id,
            expires_at=record.expires_at,
            status=status,
            result=result if result is not None else record.result,
            lease_owner=None if status != "in_progress" else record.lease_owner,
            lease_expires_at=None if status != "in_progress" else record.lease_expires_at,
            fencing_token=record.fencing_token,
        )

    def claim(self, task_id: str, *, worker_id: str, lease_expires_at: int) -> int | None:
        record = self._records.get(task_id)
        if record is None or record.status != "pending":
            return None
        fencing_token = (record.fencing_token or 0) + 1
        self._records[task_id] = TaskRecord(
            record.task_id,
            record.user_id,
            record.expires_at,
            "in_progress",
            record.result,
            worker_id,
            lease_expires_at,
            fencing_token,
        )
        return fencing_token

    def renew(
        self,
        task_id: str,
        *,
        worker_id: str,
        fencing_token: int,
        lease_expires_at: int,
        now: int,
    ) -> bool:
        record = self._records.get(task_id)
        if (
            record is None
            or record.status != "in_progress"
            or record.lease_owner != worker_id
            or record.fencing_token != fencing_token
            or record.lease_expires_at is None
            or record.lease_expires_at <= now
        ):
            return False
        self._records[task_id] = TaskRecord(
            record.task_id,
            record.user_id,
            record.expires_at,
            record.status,
            record.result,
            record.lease_owner,
            lease_expires_at,
            record.fencing_token,
        )
        return True

    def finish(
        self,
        task_id: str,
        *,
        worker_id: str,
        fencing_token: int,
        status: str,
        result: dict[str, str] | None = None,
        now: int,
    ) -> bool:
        record = self._records.get(task_id)
        if (
            record is None
            or record.status != "in_progress"
            or record.lease_owner != worker_id
            or record.fencing_token != fencing_token
            or record.lease_expires_at is None
            or record.lease_expires_at <= now
        ):
            return False
        self.update(task_id, status=status, result=result)
        return True

    def count_active(self, user_id: str) -> int:
        return sum(
            record.user_id == user_id and record.status in {"pending", "in_progress"}
            for record in self._records.values()
        )

    def expire(self, now: int) -> None:
        for task_id, record in tuple(self._records.items()):
            lease_expired = (
                record.status == "in_progress"
                and record.lease_expires_at is not None
                and record.lease_expires_at <= now
            )
            if record.status in {"pending", "in_progress"} and (record.expires_at <= now or lease_expired):
                if record.status == "in_progress" and record.lease_expires_at is not None:
                    self.update(task_id, status="recovery_required")
                else:
                    self.update(task_id, status="expired")

    def close(self) -> None:
        return None


class SQLiteTaskStore:
    """Durable local task state; interrupted work becomes recovery-required."""

    def __init__(self, database: str) -> None:
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mcp_tasks (
                task_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                lease_owner TEXT,
                lease_expires_at INTEGER,
                fencing_token INTEGER,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {row[1] for row in self._connection.execute("PRAGMA table_info(mcp_tasks)")}
        if "lease_owner" not in columns:
            self._connection.execute("ALTER TABLE mcp_tasks ADD COLUMN lease_owner TEXT")
        if "lease_expires_at" not in columns:
            self._connection.execute("ALTER TABLE mcp_tasks ADD COLUMN lease_expires_at INTEGER")
        if "fencing_token" not in columns:
            self._connection.execute("ALTER TABLE mcp_tasks ADD COLUMN fencing_token INTEGER")
        self._connection.execute(
            """
            UPDATE mcp_tasks
            SET status = 'recovery_required', updated_at = ?
            WHERE status = 'in_progress'
            """,
            (datetime.now(timezone.utc).isoformat(),),
        )
        self._connection.commit()

    def create(self, record: TaskRecord) -> None:
        self._connection.execute(
            """
            INSERT INTO mcp_tasks (task_id, user_id, expires_at, status, result_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.task_id,
                record.user_id,
                record.expires_at,
                record.status,
                json.dumps(record.result, sort_keys=True, separators=(",", ":"))
                if record.result is not None
                else None,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._connection.commit()

    def get(self, task_id: str) -> TaskRecord | None:
        row = self._connection.execute(
            """
            SELECT task_id, user_id, expires_at, status, result_json, lease_owner, lease_expires_at, fencing_token
            FROM mcp_tasks WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        return TaskRecord(
            task_id=row[0],
            user_id=row[1],
            expires_at=row[2],
            status=row[3],
            result=json.loads(row[4]) if row[4] else None,
            lease_owner=row[5],
            lease_expires_at=row[6],
            fencing_token=row[7],
        )

    def update(self, task_id: str, *, status: str, result: dict[str, str] | None = None) -> None:
        record = self.get(task_id)
        if record is None:
            raise ValueError("MCP task does not exist")
        self._connection.execute(
            """
            UPDATE mcp_tasks
            SET status = ?, result_json = ?, updated_at = ?
            WHERE task_id = ?
            """,
            (
                status,
                json.dumps(result, sort_keys=True, separators=(",", ":"))
                if result is not None
                else json.dumps(record.result, sort_keys=True, separators=(",", ":"))
                if record.result is not None
                else None,
                datetime.now(timezone.utc).isoformat(),
                task_id,
            ),
        )
        self._connection.commit()

    def claim(self, task_id: str, *, worker_id: str, lease_expires_at: int) -> int | None:
        cursor = self._connection.execute(
            """
            UPDATE mcp_tasks
            SET status = 'in_progress', lease_owner = ?, lease_expires_at = ?,
                fencing_token = COALESCE(fencing_token, 0) + 1, updated_at = ?
            WHERE task_id = ? AND status = 'pending'
            """,
            (worker_id, lease_expires_at, datetime.now(timezone.utc).isoformat(), task_id),
        )
        self._connection.commit()
        if cursor.rowcount != 1:
            return None
        return self.get(task_id).fencing_token

    def renew(
        self,
        task_id: str,
        *,
        worker_id: str,
        fencing_token: int,
        lease_expires_at: int,
        now: int,
    ) -> bool:
        cursor = self._connection.execute(
            """
            UPDATE mcp_tasks
            SET lease_expires_at = ?, updated_at = ?
            WHERE task_id = ? AND status = 'in_progress' AND lease_owner = ?
              AND fencing_token = ? AND lease_expires_at > ?
            """,
            (
                lease_expires_at,
                datetime.now(timezone.utc).isoformat(),
                task_id,
                worker_id,
                fencing_token,
                now,
            ),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def finish(
        self,
        task_id: str,
        *,
        worker_id: str,
        fencing_token: int,
        status: str,
        result: dict[str, str] | None = None,
        now: int,
    ) -> bool:
        record = self.get(task_id)
        if record is None:
            return False
        result_json = (
            json.dumps(result, sort_keys=True, separators=(",", ":"))
            if result is not None
            else json.dumps(record.result, sort_keys=True, separators=(",", ":"))
            if record.result is not None
            else None
        )
        cursor = self._connection.execute(
            """
            UPDATE mcp_tasks
                        SET status = ?, result_json = ?, lease_owner = NULL, lease_expires_at = NULL, updated_at = ?
                        WHERE task_id = ? AND status = 'in_progress' AND lease_owner = ?
                            AND fencing_token = ? AND lease_expires_at > ?
            """,
                        (
                                status,
                                result_json,
                                datetime.now(timezone.utc).isoformat(),
                                task_id,
                                worker_id,
                                fencing_token,
                                now,
                        ),
        )
        self._connection.commit()
        return cursor.rowcount == 1

    def count_active(self, user_id: str) -> int:
        return self._connection.execute(
            """
            SELECT COUNT(*) FROM mcp_tasks
            WHERE user_id = ? AND status IN ('pending', 'in_progress')
            """,
            (user_id,),
        ).fetchone()[0]

    def expire(self, now: int) -> None:
        self._connection.execute(
            """
                        UPDATE mcp_tasks
                        SET status = CASE WHEN status = 'in_progress' THEN 'recovery_required' ELSE 'expired' END,
                                lease_owner = NULL, lease_expires_at = NULL, updated_at = ?
                        WHERE status IN ('pending', 'in_progress')
                            AND (expires_at <= ? OR (status = 'in_progress' AND lease_expires_at <= ?))
            """,
                        (datetime.now(timezone.utc).isoformat(), now, now),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
