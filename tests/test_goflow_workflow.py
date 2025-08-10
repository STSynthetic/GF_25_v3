import asyncio
from typing import Any

import pytest

from app.services.goflow_workflow import GoFlowWorkflow, ProcessResult
from app.api.goflow_models import Job, JobStatusUpdate


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []
        self.job: Job | None = Job(
            job_id="j1",
            project_id="p1",
            media_id="m1",
            analysis_id="a1",
            payload={"x": 1},
        )

    async def __aenter__(self):  # pragma: no cover
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover
        return None

    async def get_next_job(self) -> Job:
        if self.job is None:
            raise RuntimeError("no job")
        self.calls.append(("get_next_job", None))
        return self.job

    async def update_project_status(self, project_id: str, update: JobStatusUpdate):
        self.calls.append(("update_status", (project_id, update.status, update.progress)))
        return {"ok": True}

    async def submit_analysis_result(self, payload):
        self.calls.append(("submit", payload.model_dump()))
        return {"ok": True}

    async def generate_project_report(self, req):
        self.calls.append(("report", req.model_dump()))
        return type(
            "Rep", (), {"project_id": req.project_id, "report_id": "r1", "status": "queued"}
        )()


@pytest.mark.asyncio
async def test_workflow_success_path():
    client = FakeClient()
    wf = GoFlowWorkflow(client)

    async def process(job: Job) -> ProcessResult:
        assert job.job_id == "j1"
        await asyncio.sleep(0)  # allow scheduling
        return ProcessResult(result={"score": 0.8}, meta={"note": "ok"})

    processed = await wf.run_once(process)
    assert processed is True

    # Verify critical calls occurred
    methods = [m for m, _ in client.calls]
    assert methods[:3] == ["get_next_job", "update_status", "submit"]
    assert "report" in methods


@pytest.mark.asyncio
async def test_workflow_failure_path():
    client = FakeClient()
    wf = GoFlowWorkflow(client)

    async def process_fail(job: Job) -> ProcessResult:
        raise RuntimeError("boom")

    processed = await wf.run_once(process_fail)
    assert processed is True  # A job was acquired even if failed

    # Ensure a failed status update was attempted
    failed_updates = [c for c in client.calls if c[0] == "update_status" and c[1][1] == "failed"]
    assert failed_updates, client.calls
