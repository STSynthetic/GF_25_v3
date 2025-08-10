import pytest

from app.db import schema
from app.db.connection import dispose_engine, get_engine
from app.services.state_service import (
    CompleteProcessRequest,
    LogQAAttemptRequest,
    StartProcessRequest,
    StartTaskRequest,
    StateService,
    UpdateTaskStatusRequest,
)


@pytest.mark.asyncio
async def test_state_service_lifecycle(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

    engine = await get_engine()

    # create tables
    async with engine.begin() as conn:
        await conn.run_sync(schema.metadata.create_all)

    svc = StateService()

    # Start task
    resp = await svc.start_task(StartTaskRequest(analysis_type="themes"))
    assert resp.task_id

    # Update task status
    await svc.update_task_status(UpdateTaskStatusRequest(task_id=resp.task_id, status="running"))

    # Start process
    p = await svc.start_process(
        StartProcessRequest(
            task_id=resp.task_id,
            worker_id="w1",
            state="started",
        )
    )
    assert p.process_id

    # Log QA attempt
    attempt_id = await svc.log_qa_attempt(
        LogQAAttemptRequest(
            task_id=resp.task_id,
            qa_stage="structural",
            validation_result={"ok": True},
        )
    )
    assert attempt_id

    # Complete process
    await svc.complete_process(CompleteProcessRequest(process_id=p.process_id, success=True))

    # Audit trail should have at least 2 entries (started + completed)
    logs = await svc.get_audit_trail(p.process_id)
    assert len(logs) >= 2

    await dispose_engine()
