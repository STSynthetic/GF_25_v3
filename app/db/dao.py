from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.connection import get_sessionmaker


# Simple in-process TTL cache for frequently accessed reads
class _TTLCache:
    def __init__(self, ttl_seconds: float = 5.0) -> None:
        self.ttl = ttl_seconds
        self.store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        now = time.time()
        item = self.store.get(key)
        if not item:
            return None
        ts, value = item
        if now - ts > self.ttl:
            self.store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self.store[key] = (time.time(), value)

    def invalidate(self, key: str) -> None:
        self.store.pop(key, None)


_task_cache = _TTLCache(ttl_seconds=5.0)
_audit_cache = _TTLCache(ttl_seconds=5.0)


def _uuid() -> str:
    return uuid.uuid4().hex


def _is_sqlite() -> bool:
    url = os.getenv("DATABASE_URL", "")
    return url.startswith("sqlite+") or url.startswith("sqlite:")


def _json_param(value: Any) -> Any:
    if value is None:
        return None
    # For SQLite we must serialize to string; Postgres JSONB accepts dicts
    return json.dumps(value) if _is_sqlite() else value


class TaskStateDAO:
    async def create_task(self, analysis_type: str, status: str) -> str:
        task_id = _uuid()
        Session = get_sessionmaker()
        async with Session() as session:
            await self._create_task(session, task_id, analysis_type, status)
        return task_id

    async def _create_task(
        self, session: AsyncSession, task_id: str, analysis_type: str, status: str
    ) -> None:
        q = text(
            """
            insert into tasks (task_id, analysis_type, status, created_at, updated_at)
            values (:task_id, :analysis_type, :status, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        )
        try:
            await session.execute(
                q,
                {
                    "task_id": task_id,
                    "analysis_type": analysis_type,
                    "status": status,
                },
            )
            await session.commit()
            _task_cache.invalidate(task_id)
        except IntegrityError as e:
            await session.rollback()
            raise e

    async def update_task_status(self, task_id: str, status: str) -> None:
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                update tasks set status=:status, updated_at=CURRENT_TIMESTAMP
                where task_id=:task_id
                """
            )
            res = await session.execute(q, {"task_id": task_id, "status": status})
            await session.commit()
            if res.rowcount == 0:
                raise KeyError(f"task not found: {task_id}")
            _task_cache.invalidate(task_id)

    async def get_task_by_id(self, task_id: str) -> dict[str, Any] | None:
        cached = _task_cache.get(task_id)
        if cached is not None:
            return cached
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                select task_id, analysis_type, status, created_at, updated_at
                from tasks where task_id=:task_id
                """
            )
            res = await session.execute(q, {"task_id": task_id})
            row = res.mappings().first()
            if row is None:
                return None
            data = dict(row)
            _task_cache.set(task_id, data)
            return data


class ProcessStateDAO:
    async def create_process_state(self, task_id: str, worker_id: str, state: str) -> str:
        process_id = _uuid()
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                insert into processing_state (process_id, task_id, worker_id, state, started_at)
                values (:process_id, :task_id, :worker_id, :state, CURRENT_TIMESTAMP)
                """
            )
            try:
                await session.execute(
                    q,
                    {
                        "process_id": process_id,
                        "task_id": task_id,
                        "worker_id": worker_id,
                        "state": state,
                    },
                )
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                raise e
        return process_id

    async def update_process_status(self, process_id: str, state: str) -> None:
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                update processing_state set state=:state, finished_at=
                    case when :state in ('completed','failed') then
                        CURRENT_TIMESTAMP
                    else finished_at end
                where process_id=:process_id
                """
            )
            res = await session.execute(q, {"process_id": process_id, "state": state})
            await session.commit()
            if res.rowcount == 0:
                raise KeyError(f"process not found: {process_id}")

    async def get_process_by_id(self, process_id: str) -> dict[str, Any] | None:
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                select process_id, task_id, worker_id, state, started_at, finished_at
                from processing_state where process_id=:process_id
                """
            )
            res = await session.execute(q, {"process_id": process_id})
            row = res.mappings().first()
            return dict(row) if row else None


class QAAttemptDAO:
    async def log_qa_attempt(
        self,
        task_id: str,
        qa_stage: str,
        validation_result: dict[str, Any],
        failure_reasons: dict[str, Any] | None = None,
        corrective_prompt_used: str | None = None,
    ) -> str:
        attempt_id = _uuid()
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                insert into qa_attempts (
                    attempt_id,
                    task_id,
                    qa_stage,
                    validation_result,
                    failure_reasons,
                    corrective_prompt_used,
                    created_at
                ) values (
                    :attempt_id,
                    :task_id,
                    :qa_stage,
                    :validation_result,
                    :failure_reasons,
                    :corrective_prompt_used,
                    CURRENT_TIMESTAMP
                )
                """
            )
            try:
                await session.execute(
                    q,
                    {
                        "attempt_id": attempt_id,
                        "task_id": task_id,
                        "qa_stage": qa_stage,
                        "validation_result": _json_param(validation_result),
                        "failure_reasons": _json_param(failure_reasons),
                        "corrective_prompt_used": corrective_prompt_used,
                    },
                )
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                raise e
        return attempt_id

    async def get_attempt_count_for_task(self, task_id: str) -> int:
        Session = get_sessionmaker()
        async with Session() as session:
            q = text("select count(*) from qa_attempts where task_id=:task_id")
            res = await session.execute(q, {"task_id": task_id})
            return int(res.scalar_one())


class AuditLogDAO:
    async def create_audit_log(
        self,
        process_id: str,
        event_type: str,
        event_data: dict[str, Any] | None = None,
    ) -> str:
        log_id = _uuid()
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                insert into audit_logs (log_id, process_id, event_type, event_data, timestamp)
                values (:log_id, :process_id, :event_type, :event_data, CURRENT_TIMESTAMP)
                """
            )
            try:
                await session.execute(
                    q,
                    {
                        "log_id": log_id,
                        "process_id": process_id,
                        "event_type": event_type,
                        "event_data": _json_param(event_data),
                    },
                )
                await session.commit()
                _audit_cache.invalidate(process_id)
            except IntegrityError as e:
                await session.rollback()
                raise e
        return log_id

    async def get_audit_logs_by_process(self, process_id: str) -> list[dict[str, Any]]:
        cached = _audit_cache.get(process_id)
        if cached is not None:
            return cached
        Session = get_sessionmaker()
        async with Session() as session:
            q = text(
                """
                select log_id, process_id, event_type, event_data, timestamp
                from audit_logs where process_id=:process_id order by timestamp asc
                """
            )
            res = await session.execute(q, {"process_id": process_id})
            rows = [dict(r) for r in res.mappings().all()]
            _audit_cache.set(process_id, rows)
            return rows
