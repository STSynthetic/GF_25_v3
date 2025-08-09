from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.config_schema import QAStage


class ValidationContext(BaseModel):
    """Shared context passed between QA stages."""

    analysis_type: str = Field(description="Analysis type identifier")
    config_version: str = Field(description="Version of the config used")
    original_response: str = Field(description="Model response to validate/correct")
    image_b64: str | None = Field(default=None, description="Optional base64 image data")


class ValidationResult(BaseModel):
    """Normalized QA result model per [TYPE-SAFETY]."""

    stage: QAStage = Field(description="QA stage that produced this result")
    passed: bool = Field(description="Did this stage's checks pass?")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0..1")
    issues: list[str] = Field(default_factory=list, description="Detected issues or notes")
    corrected_output: str | None = Field(
        default=None, description="If corrections applied, the corrected JSON string"
    )


class AgentConfig(BaseModel):
    """Configuration for QA agents (timeouts, model params, etc)."""

    timeout_seconds: int = Field(ge=1, le=120, default=60, description="Agent timeout")
    model: str = Field(default="ollama/qwen2.5vl:latest", description="Model name")
    temperature: float = Field(ge=0.0, le=2.0, default=0.05, description="Sampling temp")
    num_ctx: int = Field(ge=1024, default=32768, description="Context window tokens")


class BaseQAAgent(ABC):
    """Abstract base for specialized QA agents."""

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()

    @abstractmethod
    async def validate(self, ctx: ValidationContext) -> ValidationResult:  # pragma: no cover
        ...


__all__ = [
    "QAStage",
    "ValidationContext",
    "ValidationResult",
    "AgentConfig",
    "BaseQAAgent",
]
