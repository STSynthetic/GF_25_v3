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
    # Support task spec "max_tokens" while aligning with PRD's num_predict
    num_predict: int | None = Field(
        default=None,
        ge=0,
        description="Maximum tokens to generate (alias: max_tokens)",
        alias="max_tokens",
    )


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
    worker_count: int | None = Field(
        default=None,
        ge=1,
        le=128,
        description="Number of workers to allocate (optional)",
    )
    batch_size: int | None = Field(
        default=None,
        ge=1,
        le=1024,
        description="Batch size for grouped processing (optional)",
    )
    timeout_seconds: int | None = Field(
        default=None,
        ge=1,
        description="Timeout per work item in seconds (optional)",
    )


class Prompts(BaseModel):
    system_prompt: str = Field(min_length=1, description="System prompt text")
    user_prompt: str = Field(min_length=1, description="User prompt template text")


class ValidationConstraints(BaseModel):
    rules: list[str] = Field(default_factory=list, description="Validation rules to enforce")
    output_format: str | None = Field(
        default=None,
        description="Expected output format (e.g., json, yaml)",
    )
    required_fields: list[str] | None = Field(
        default=None,
        description="List of required fields expected in the model output",
    )
    data_types: dict[str, str] | None = Field(
        default=None,
        description="Mapping of output fields to expected data types",
    )


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
    max_latency_ms: int | None = Field(
        default=None,
        ge=1,
        description="Maximum acceptable end-to-end latency in milliseconds",
    )
    min_accuracy: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum acceptable accuracy threshold (0.0-1.0)",
    )
    throughput_goals: list[str] | None = Field(
        default=None,
        description="List of descriptive throughput goals",
    )


class Metadata(BaseModel):
    name: str = Field(description="Human-friendly configuration name")
    version: str = Field(min_length=1, description="Configuration version")
    description: str = Field(description="Configuration description")
    analysis_type: "AnalysisType" = Field(description="One of 21 supported analysis types")


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
    # Optional metadata block for future alignment; kept optional for backward compatibility
    metadata: Metadata | None = Field(
        default=None,
        description="Optional metadata block mirroring top-level fields",
    )

    @field_validator("qa_stages")
    @classmethod
    def ensure_all_stages_unique(cls, v: list[QAStage]) -> list[QAStage]:
        if len(v) != len(set(v)):
            raise ValueError("qa_stages must be unique")
        return v

    @field_validator("metadata")
    @classmethod
    def validate_metadata_consistency(cls, meta: Metadata | None, values):  # type: ignore[override]
        # If metadata is provided, ensure consistency with top-level fields when present
        if meta is None:
            return meta
        # best-effort consistency checks; do not raise if top-level missing
        top_analysis_type = values.get("analysis_type")
        top_version = values.get("version")
        if top_analysis_type and meta.analysis_type != top_analysis_type:
            raise ValueError("metadata.analysis_type must match analysis_type")
        if top_version and meta.version != top_version:
            raise ValueError("metadata.version must match version")
        return meta
