from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Job(BaseModel):
    job_id: str = Field(description="Unique job identifier")
    project_id: str = Field(description="Project identifier")
    media_id: str = Field(description="Media identifier")
    analysis_id: str = Field(description="Analysis identifier")
    payload: dict[str, Any] | None = Field(
        default=None, description="Optional job-specific payload"
    )


class JobStatus(str):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStatusUpdate(BaseModel):
    status: str = Field(description="New job status")
    detail: str | None = Field(default=None, description="Optional detail message")
    progress: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Optional progress 0..1"
    )


class ResultPayload(BaseModel):
    """Typed payload sent when submitting analysis results."""

    project_id: str = Field(description="Project identifier")
    media_id: str = Field(description="Media identifier")
    analysis_id: str = Field(description="Analysis identifier")
    result: dict[str, Any] = Field(description="Structured analysis result data")
    meta: dict[str, Any] | None = Field(default=None, description="Optional metadata")


class ReportRequest(BaseModel):
    project_id: str = Field(description="Project identifier")
    include_details: bool = Field(default=True, description="Include detailed sections")


class ReportResponse(BaseModel):
    project_id: str = Field(description="Project identifier")
    report_id: str = Field(description="Generated report identifier")
    status: str = Field(description="Report generation status")
