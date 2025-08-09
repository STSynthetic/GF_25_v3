from enum import Enum

from pydantic import BaseModel, Field


class ModelName(str, Enum):
    QWEN_VL_32B = "qwen2.5vl:32b"
    QWEN_VL_LATEST = "qwen2.5vl:latest"


class ModelConfig(BaseModel):
    model: str = Field(description="Model identifier for Ollama")
    temperature: float = Field(ge=0.0, le=2.0, description="Temperature for generation")
    num_ctx: int = Field(ge=1024, description="Context window tokens")


ANALYSIS_MODEL = ModelConfig(
    model=ModelName.QWEN_VL_32B.value,
    temperature=0.1,
    num_ctx=32768,
)

QA_MODEL = ModelConfig(
    model=ModelName.QWEN_VL_LATEST.value,
    temperature=0.05,
    num_ctx=32768,
)
