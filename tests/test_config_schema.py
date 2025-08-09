import pytest
from pydantic import ValidationError

from app.config_schema import (
    AnalysisConfig,
    AnalysisType,
    ModelConfiguration,
    ParallelProcessing,
    PerformanceTargets,
    Prompts,
    QAStage,
    ValidationConstraints,
    VisionOptimization,
)


def make_valid_config() -> AnalysisConfig:
    return AnalysisConfig(
        analysis_type=AnalysisType.ACTIVITIES,
        version="1.0.0",
        model_configuration=ModelConfiguration(
            model="qwen2.5vl:32b",
            temperature=0.1,
            top_p=0.9,
            top_k=40,
            num_ctx=32768,
        ),
        vision_optimization=VisionOptimization(
            max_edge_pixels=1344,
            preserve_aspect_ratio=True,
        ),
        parallel_processing=ParallelProcessing(max_concurrency=8),
        prompts=Prompts(
            system_prompt="system...",
            user_prompt="user...",
        ),
        validation_constraints=ValidationConstraints(
            rules=[
                "no meta-descriptive language",
                "json output only",
            ]
        ),
        performance_targets=PerformanceTargets(
            throughput_target="800+ per worker acceptable",
            success_rate_target=0.95,
        ),
    )


def test_valid_config_passes():
    cfg = make_valid_config()
    assert cfg.analysis_type == AnalysisType.ACTIVITIES
    assert cfg.parallel_processing.max_concurrency == 8
    # default QA stages include all three in order
    assert cfg.qa_stages == [
        QAStage.STRUCTURAL,
        QAStage.CONTENT_QUALITY,
        QAStage.DOMAIN_EXPERT,
    ]


def test_invalid_duplicate_qa_stages_rejected():
    cfg = make_valid_config()
    # Introduce duplicates
    cfg.qa_stages = [QAStage.STRUCTURAL, QAStage.STRUCTURAL]
    with pytest.raises(ValueError):
        # re-validate by constructing again
        AnalysisConfig(**cfg.model_dump())


def test_bounds_enforced():
    with pytest.raises(ValidationError):
        ModelConfiguration(
            model="qwen2.5vl:32b",
            temperature=3.5,  # > 2.0
            top_p=0.9,
            top_k=40,
            num_ctx=32768,
        )
    with pytest.raises(ValidationError):
        VisionOptimization(max_edge_pixels=32, preserve_aspect_ratio=True)  # < 64
    with pytest.raises(ValidationError):
        ParallelProcessing(max_concurrency=0)  # < 1
