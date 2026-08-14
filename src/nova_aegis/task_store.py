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


class TaskStore(Protocol):
    def create(self, record: TaskRecord) -> None: ...

    def get(self, task_id: str) -> TaskRecord | None: ...

    def update(self, task_id: str, *, status: str, result: dict[str, str] | None = None) -> None: ...

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
        )

    def count_active(self, user_id: str) -> int:
        return sum(
            record.user_id == user_id and record.status in {"pending", "in_progress"}
            for record in self._records.values()
        )

    def expire(self, now: int) -> None:
        for task_id, record in tuple(self._records.items()):
            if record.status in {"pending", "in_progress"} and record.expires_at <= now:
                self.update(task_id, status="expired")

    def close(self) -> None:
        return None


class SQLiteTaskStore:
    """Durable local task state; interrupted work becomes recovery-required."""

    def __init__(self, database: str) -> None:
        self._connection = sqlite3.connect(database)
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS mcp_tasks (
                task_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
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
            SELECT task_id, user_id, expires_at, status, result_json
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
            SET status = 'expired', updated_at = ?
            WHERE status IN ('pending', 'in_progress') AND expires_at <= ?
            """,
            (datetime.now(timezone.utc).isoformat(), now),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
