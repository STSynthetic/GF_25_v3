import pytest
from sqlalchemy import text

from app.db import schema
from app.db.connection import dispose_engine, get_engine
from app.db.dao import AuditLogDAO, QAAttemptDAO, TaskStateDAO, TransactionManager


@pytest.mark.asyncio
async def test_batch_operations_and_transaction_management(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    engine = await get_engine()

    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(schema.metadata.create_all)

    task_dao = TaskStateDAO()
    qa_dao = QAAttemptDAO()
    audit_dao = AuditLogDAO()

    # Bulk insert tasks
    items = [
        ("t1", "themes", "pending"),
        ("t2", "ages", "pending"),
    ]
    created_ids = await task_dao.create_tasks_bulk(items)
    assert created_ids == ["t1", "t2"]

    # Bulk QA attempts
    attempt_ids = await qa_dao.log_qa_attempts_bulk(
        [
            {
                "task_id": "t1",
                "qa_stage": "structural",
                "validation_result": {"ok": True},
            },
            {
                "task_id": "t2",
                "qa_stage": "content_quality",
                "validation_result": {"ok": False},
                "failure_reasons": {"missing": ["field"]},
            },
        ]
    )
    assert len(attempt_ids) == 2

    # Bulk audit logs
    log_ids = await audit_dao.create_audit_logs_bulk(
        [
            {"process_id": "p1", "event_type": "start", "event_data": {"w": 1}},
            {"process_id": "p1", "event_type": "finish", "event_data": {"ok": True}},
        ]
    )
    assert len(log_ids) == 2

    # TransactionManager commit and rollback
    # Commit case
    async with TransactionManager() as session:
        await session.execute(
            text(
                "insert into tasks (task_id, analysis_type, status, created_at, updated_at) "
                "values (:t, 'themes', 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"t": "t3"},
        )
    # Row should exist after commit
    async with engine.connect() as conn:
        res = await conn.execute(text("select count(*) from tasks where task_id='t3'"))
        assert int(res.scalar_one()) == 1

    # Rollback case
    with pytest.raises(Exception):
        async with TransactionManager() as session:
            await session.execute(
                text(
                    "insert into tasks (task_id, analysis_type, status, created_at, updated_at) "
                    "values ('t4', 'themes', 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
            # Force error (duplicate primary key) to trigger rollback
            await session.execute(
                text(
                    "insert into tasks (task_id, analysis_type, status, created_at, updated_at) "
                    "values ('t4', 'themes', 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                )
            )
    # Ensure rollback happened (no second row created; only one row 't4' should not persist)
    async with engine.connect() as conn:
        res = await conn.execute(text("select count(*) from tasks where task_id='t4'"))
        assert int(res.scalar_one()) == 0

    await dispose_engine()
