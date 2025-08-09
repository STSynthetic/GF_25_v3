from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AnalysisType(str, Enum):
    ACTIVITIES = "activities"
    AGES = "ages"
    BODY_SHAPES = "body_shapes"
    CAPTIONS = "captions"
    CATEGORY = "category"
    COLORS = "colors"
    COMPOSITION = "composition"
    EMOTIONS = "emotions"
    ETHNICITY = "ethnicity"
    EVENTS = "events"
    GENDER = "gender"
    LIGHTING = "lighting"
    LOCATIONS = "locations"
    OBJECTS = "objects"
    OCCLUSIONS = "occlusions"
    OUTFITS = "outfits"
    RELATIONSHIPS = "relationships"
    SCENE_DESCRIPTION = "scene_description"
    THEMES = "themes"
    TIME_OF_DAY = "time_of_day"
    WEATHER = "weather"


class QAStage(str, Enum):
    STRUCTURAL = "structural"
    CONTENT_QUALITY = "content_quality"
    DOMAIN_EXPERT = "domain_expert"


class ModelConfiguration(BaseModel):
    model: str = Field(description="Base model id, e.g. qwen2.5vl:32b")
    temperature: float = Field(ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(ge=0.0, le=1.0, description="Top-p nucleus sampling")
    top_k: int = Field(ge=0, description="Top-k sampling cutoff")
    num_ctx: int = Field(ge=128, description="Context window size (tokens)")


class VisionOptimization(BaseModel):
    max_edge_pixels: int = Field(
        ge=64,
        le=4096,
        description="Max longest image edge in pixels",
    )
    preserve_aspect_ratio: bool = Field(
        description="Whether to preserve aspect ratio during resize",
    )


class ParallelProcessing(BaseModel):
    max_concurrency: int = Field(ge=1, le=64, description="Max concurrent analyses")


class Prompts(BaseModel):
    system_prompt: str = Field(min_length=1, description="System prompt text")
    user_prompt: str = Field(min_length=1, description="User prompt template text")


class ValidationConstraints(BaseModel):
    rules: list[str] = Field(default_factory=list, description="Validation rules to enforce")


class PerformanceTargets(BaseModel):
    throughput_target: str | None = Field(
        default=None,
        description="Non-committal throughput target guidance (e.g., '800+ per worker acceptable')",
    )
    success_rate_target: float = Field(
        ge=0.0,
        le=1.0,
        description="Target success rate for corrective processing (e.g., 0.95 for 95%)",
        default=0.95,
    )


class AnalysisConfig(BaseModel):
    analysis_type: AnalysisType = Field(description="One of 21 supported analysis types")
    version: str = Field(min_length=1, description="Config version identifier")

    model_configuration: ModelConfiguration = Field(description="Model parameters")
    vision_optimization: VisionOptimization = Field(description="Vision preprocessing settings")
    parallel_processing: ParallelProcessing = Field(description="Concurrency controls")

    prompts: Prompts = Field(
        description="Prompts block (no hardcoded prompts in code)",
    )
    validation_constraints: ValidationConstraints = Field(
        description="Validation constraints block",
    )
    performance_targets: PerformanceTargets = Field(description="Performance targets block")

    qa_stages: list[QAStage] = Field(
        default_factory=lambda: [
            QAStage.STRUCTURAL,
            QAStage.CONTENT_QUALITY,
            QAStage.DOMAIN_EXPERT,
        ],
        description="QA stages to run in order",
    )

    @field_validator("qa_stages")
    @classmethod
    def ensure_all_stages_unique(cls, v: list[QAStage]) -> list[QAStage]:
        if len(v) != len(set(v)):
            raise ValueError("qa_stages must be unique")
        return v
