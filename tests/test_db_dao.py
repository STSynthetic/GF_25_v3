import pytest
from sqlalchemy import text

from app.db import schema
from app.db.connection import dispose_engine, get_engine
from app.db.dao import AuditLogDAO, ProcessStateDAO, QAAttemptDAO, TaskStateDAO


@pytest.mark.asyncio
async def test_dao_crud_sqlite_aiosqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    engine = await get_engine()

    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(schema.metadata.create_all)

    # sanity select
    async with engine.connect() as conn:
        res = await conn.execute(text("select 1"))
        assert res.scalar_one() == 1

    # DAOs
    task_dao = TaskStateDAO()
    proc_dao = ProcessStateDAO()
    qa_dao = QAAttemptDAO()
    audit_dao = AuditLogDAO()

    # Create task
    task_id = await task_dao.create_task(analysis_type="themes", status="pending")
    task = await task_dao.get_task_by_id(task_id)
    assert task and task["status"] == "pending"

    # Update task status
    await task_dao.update_task_status(task_id, "running")
    task2 = await task_dao.get_task_by_id(task_id)
    assert task2 and task2["status"] == "running"

    # Create process
    process_id = await proc_dao.create_process_state(
        task_id=task_id,
        worker_id="worker-1",
        state="started",
    )
    proc = await proc_dao.get_process_by_id(process_id)
    assert proc and proc["task_id"] == task_id

    # Update process status
    await proc_dao.update_process_status(process_id, "completed")
    proc2 = await proc_dao.get_process_by_id(process_id)
    assert proc2 and proc2["state"] == "completed"

    # QA attempt
    attempt_id = await qa_dao.log_qa_attempt(
        task_id=task_id,
        qa_stage="structural",
        validation_result={"ok": True},
    )
    assert attempt_id
    cnt = await qa_dao.get_attempt_count_for_task(task_id)
    assert cnt == 1

    # Audit log
    log_id = await audit_dao.create_audit_log(
        process_id=process_id,
        event_type="worker.finish",
        event_data={"result": "success"},
    )
    assert log_id
    logs = await audit_dao.get_audit_logs_by_process(process_id)
    assert len(logs) == 1 and logs[0]["event_type"] == "worker.finish"

    await dispose_engine()
