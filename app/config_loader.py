from __future__ import annotations

from pathlib import Path

import yaml

from app.config_schema import AnalysisConfig, AnalysisType


class ConfigRegistry:
    """In-memory registry for analysis configurations with refresh capability."""

    def __init__(self) -> None:
        self._configs: dict[AnalysisType, AnalysisConfig] = {}

    def load_config(self, path: Path) -> AnalysisConfig:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        cfg = AnalysisConfig(**data)
        return cfg

    def load_all_configs(self, directory: Path) -> dict[AnalysisType, AnalysisConfig]:
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Config directory not found: {directory}")
        found: dict[AnalysisType, AnalysisConfig] = {}
        for yml in sorted(directory.glob("*.yaml")):
            cfg = self.load_config(yml)
            if cfg.analysis_type in found:
                raise ValueError(
                    f"Duplicate analysis_type '{cfg.analysis_type.value}' in {yml.name}"
                )
            found[cfg.analysis_type] = cfg
        self._configs = found
        return self._configs

    def get(self, analysis_type: AnalysisType) -> AnalysisConfig:
        return self._configs[analysis_type]

    def refresh(self, directory: Path) -> dict[AnalysisType, AnalysisConfig]:
        return self.load_all_configs(directory)


# Convenience module-level helpers
_registry = ConfigRegistry()


def load_config(path: Path) -> AnalysisConfig:
    return _registry.load_config(path)


def load_all_configs(directory: Path) -> dict[AnalysisType, AnalysisConfig]:
    return _registry.load_all_configs(directory)


def get_config(analysis_type: AnalysisType) -> AnalysisConfig:
    return _registry.get(analysis_type)


def refresh_configs(directory: Path) -> dict[AnalysisType, AnalysisConfig]:
    return _registry.refresh(directory)
