from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.config_loader import ConfigRegistry
from app.config_schema import AnalysisType

VALID_YAML = {
    "analysis_type": "activities",
    "version": "1.0.0",
    "model_configuration": {
        "model": "qwen2.5vl:32b",
        "temperature": 0.1,
        "top_p": 0.9,
        "top_k": 40,
        "num_ctx": 32768,
    },
    "vision_optimization": {
        "max_edge_pixels": 1344,
        "preserve_aspect_ratio": True,
    },
    "parallel_processing": {"max_concurrency": 8},
    "prompts": {"system_prompt": "sys", "user_prompt": "user"},
    "validation_constraints": {"rules": ["no meta"]},
    "performance_targets": {
        "throughput_target": "800+ per worker acceptable",
        "success_rate_target": 0.95,
    },
}


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_load_single_config(tmp_path: Path):
    yml = tmp_path / "activities.yaml"
    write_yaml(yml, VALID_YAML)

    reg = ConfigRegistry()
    cfg = reg.load_config(yml)
    assert cfg.analysis_type == AnalysisType.ACTIVITIES


def test_load_all_configs_and_get(tmp_path: Path):
    a = tmp_path / "activities.yaml"
    b = tmp_path / "ages.yaml"
    d_a = VALID_YAML.copy()
    d_b = VALID_YAML.copy()
    d_b["analysis_type"] = "ages"
    write_yaml(a, d_a)
    write_yaml(b, d_b)

    reg = ConfigRegistry()
    loaded = reg.load_all_configs(tmp_path)
    assert set(loaded.keys()) == {AnalysisType.ACTIVITIES, AnalysisType.AGES}
    # get() returns same object
    assert reg.get(AnalysisType.AGES).analysis_type == AnalysisType.AGES


def test_invalid_schema_raises(tmp_path: Path):
    bad = tmp_path / "activities.yaml"
    data = VALID_YAML.copy()
    # remove required field
    data["model_configuration"].pop("model")
    write_yaml(bad, data)

    reg = ConfigRegistry()
    with pytest.raises(ValidationError):
        reg.load_all_configs(tmp_path)


def test_duplicate_analysis_type_rejected(tmp_path: Path):
    a = tmp_path / "activities_a.yaml"
    b = tmp_path / "activities_b.yaml"
    write_yaml(a, VALID_YAML)
    write_yaml(b, VALID_YAML)

    reg = ConfigRegistry()
    with pytest.raises(ValueError):
        reg.load_all_configs(tmp_path)
