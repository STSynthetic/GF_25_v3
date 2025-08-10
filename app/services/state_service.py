from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.db.dao import AuditLogDAO, ProcessStateDAO, QAAttemptDAO, TaskStateDAO


class StartTaskRequest(BaseModel):
    analysis_type: str = Field(description="Analysis type for the task")


class StartTaskResponse(BaseModel):
    task_id: str = Field(description="Created task identifier")


class UpdateTaskStatusRequest(BaseModel):
    task_id: str = Field(description="Task identifier")
    status: str = Field(description="New status value")


class StartProcessRequest(BaseModel):
    task_id: str = Field(description="Task identifier")
    worker_id: str = Field(description="Worker identifier handling the process")
    state: str = Field(default="started", description="Initial state of the process")


class StartProcessResponse(BaseModel):
    process_id: str = Field(description="Created process identifier")


class CompleteProcessRequest(BaseModel):
    process_id: str = Field(description="Process identifier")
    success: bool = Field(description="Whether the process completed successfully")


class LogQAAttemptRequest(BaseModel):
    task_id: str = Field(description="Task identifier")
    qa_stage: str = Field(description="QA stage (structural, content_quality, domain_expert)")
    validation_result: dict[str, Any] = Field(description="Validation result payload")
    failure_reasons: dict[str, Any] | None = Field(
        default=None, description="Optional failure reasons payload"
    )
    corrective_prompt_used: str | None = Field(
        default=None, description="Prompt used for corrective action"
    )


class StateService:
    def __init__(self) -> None:
        self.tasks = TaskStateDAO()
        self.proc = ProcessStateDAO()
        self.qa = QAAttemptDAO()
        self.audit = AuditLogDAO()

    async def start_task(self, req: StartTaskRequest) -> StartTaskResponse:
        task_id = await self.tasks.create_task(analysis_type=req.analysis_type, status="pending")
        return StartTaskResponse(task_id=task_id)

    async def update_task_status(self, req: UpdateTaskStatusRequest) -> None:
        await self.tasks.update_task_status(task_id=req.task_id, status=req.status)

    async def start_process(self, req: StartProcessRequest) -> StartProcessResponse:
        process_id = await self.proc.create_process_state(
            task_id=req.task_id, worker_id=req.worker_id, state=req.state
        )
        await self.audit.create_audit_log(
            process_id=process_id,
            event_type="process.started",
            event_data={},
        )
        return StartProcessResponse(process_id=process_id)

    async def complete_process(self, req: CompleteProcessRequest) -> None:
        new_state = "completed" if req.success else "failed"
        await self.proc.update_process_status(process_id=req.process_id, state=new_state)
        await self.audit.create_audit_log(
            process_id=req.process_id,
            event_type="process.completed" if req.success else "process.failed",
            event_data={"success": req.success},
        )

    async def log_qa_attempt(self, req: LogQAAttemptRequest) -> str:
        attempt_id = await self.qa.log_qa_attempt(
            task_id=req.task_id,
            qa_stage=req.qa_stage,
            validation_result=req.validation_result,
            failure_reasons=req.failure_reasons,
            corrective_prompt_used=req.corrective_prompt_used,
        )
        return attempt_id

    async def get_audit_trail(self, process_id: str) -> list[dict[str, Any]]:
        return await self.audit.get_audit_logs_by_process(process_id)
