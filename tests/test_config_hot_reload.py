import asyncio
from pathlib import Path

import pytest
import yaml

from app import config_hot_reload
from app.config_hot_reload import watch_and_reload_configs
from app.config_loader import ConfigRegistry
from app.config_schema import AnalysisType


@pytest.mark.asyncio
async def test_hot_reload_refreshes_registry(tmp_path: Path, monkeypatch):
    # Prepare initial config
    cfg_path = tmp_path / "activities.yaml"
    data = {
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
    cfg_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    reg = ConfigRegistry()
    stop = asyncio.Event()

    # Synchronization for mutation timing
    mutation_done = asyncio.Event()

    # Monkeypatch awatch to produce a single change event deterministically
    async def fake_awatch(_directory, debounce, force_polling):  # noqa: ARG001
        # wait until test mutates file
        await mutation_done.wait()
        # small delay to simulate debounce
        await asyncio.sleep(0.05)
        yield {("modified", str(cfg_path))}

    monkeypatch.setattr(config_hot_reload, "awatch", fake_awatch)

    # Run watcher task with small debounce for faster tests
    task = asyncio.create_task(
        watch_and_reload_configs(tmp_path, reg, debounce_ms=10, stop_event=stop)
    )

    # Allow initial load
    await asyncio.sleep(0.3)
    # registry populated and accessible via enum key
    assert reg.get(AnalysisType.ACTIVITIES).analysis_type == AnalysisType.ACTIVITIES

    # Mutate the file to trigger reload and signal watcher
    data["model_configuration"]["temperature"] = 0.2
    cfg_path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    mutation_done.set()

    # Wait shortly for watcher to process fake event
    await asyncio.sleep(0.2)
    cfg_after = reg.get(AnalysisType.ACTIVITIES)
    assert cfg_after.model_configuration.temperature == 0.2

    # Cleanup
    stop.set()
    task.cancel()
    # Task may complete gracefully depending on watcher behavior
    try:
        await task
    except asyncio.CancelledError:
        pass
