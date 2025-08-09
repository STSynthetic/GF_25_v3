from pathlib import Path

import yaml

from app.config_schema import AnalysisConfig


def test_all_yaml_configs_validate_against_schema():
    root = Path(__file__).resolve().parents[1]
    configs_dir = root / "configs"
    assert configs_dir.exists(), "configs/ directory missing"

    yaml_files = sorted(configs_dir.glob("*.yaml"))
    # Expect 21 analysis config files
    assert len(yaml_files) == 21

    for yml in yaml_files:
        with yml.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        cfg = AnalysisConfig(**data)
        assert cfg.analysis_type.value in yml.stem  # loose name alignment
