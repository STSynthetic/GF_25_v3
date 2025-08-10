from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from app.config_schema import AnalysisType, QAStage


class AgentRequest(BaseModel):
    analysis_type: AnalysisType = Field(description="Type of analysis")
    qa_stage: QAStage | None = Field(default=None, description="QA stage if applicable")
    prompt: str = Field(description="Prompt content to send to model")
    context: dict[str, Any] | None = Field(default=None, description="Optional context payload")


class AgentResponse(BaseModel):
    content: str = Field(description="Model output text content")
    confidence: float = Field(ge=0.0, le=1.0, description="Normalized confidence score")
    raw: dict[str, Any] | None = Field(default=None, description="Raw provider response payload")


class Agent(ABC):
    def __init__(self, model_cfg: dict[str, Any] | None = None) -> None:
        self.model_cfg = model_cfg or {}

    @abstractmethod
    async def run(
        self, request: AgentRequest
    ) -> AgentResponse:  # pragma: no cover (implemented by subclasses)
        raise NotImplementedError
