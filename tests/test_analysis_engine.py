import asyncio
import types
from dataclasses import dataclass
from typing import Any

import pytest

from app.config_loader import ConfigRegistry
from app.config_schema import AnalysisType
from app.services.analysis_engine import (
    AnalysisJob,
    AnalysisWorkflowEngine,
)


@pytest.fixture
def registry(tmp_path) -> ConfigRegistry:
    # Build a minimal set of YAML configs for two analysis types
    cfg_dir = tmp_path / "configs"
    cfg_dir.mkdir()

    def write_cfg(name: str):
        (cfg_dir / f"{name}.yaml").write_text(
            f"""
version: "1.0"
analysis_type: {name}
model_configuration:
  model: "ollama/qwen2.5vl:32b"
  temperature: 0.1
  top_p: 0.9
  top_k: 40
  num_ctx: 32768
vision_optimization:
  max_edge_pixels: 1024
  preserve_aspect_ratio: true
parallel_processing:
  max_concurrency: 8
prompts:
  system_prompt: "sys for {name}"
  user_prompt: "user for {name}: {{BASE64_IMAGE_PLACEHOLDER}}"
validation_constraints:
  rules: []
performance_targets:
  throughput_target: null
qa_stages:
  - structural
  - content_quality
  - domain_expert
            """,
            encoding="utf-8",
        )

    write_cfg("captions")
    write_cfg("objects")

    reg = ConfigRegistry()
    reg.load_all_configs(cfg_dir)
    return reg


@pytest.fixture(autouse=True)
async def patch_completion_async(monkeypatch):
    # Patch the model call to a controllable stub capturing params
    calls: list[dict[str, Any]] = []
    max_parallel = {"cur": 0, "max": 0}
    lock = asyncio.Lock()

    async def stub(call_args: dict[str, Any]):
        async with lock:
            max_parallel["cur"] += 1
            max_parallel["max"] = max(max_parallel["max"], max_parallel["cur"])
        # Simulate provider latency
        await asyncio.sleep(0.01)
        async with lock:
            max_parallel["cur"] -= 1
        calls.append(call_args)
        return {
            "choices": [
                {"message": {"content": "ok"}},
            ]
        }

    import app.services.analysis_engine as engine_mod

    monkeypatch.setattr(engine_mod, "completion_async", stub)
    # provide access to captured data for tests
    yield types.SimpleNamespace(calls=calls, max_parallel=max_parallel)


@pytest.mark.asyncio
async def test_run_batch_success_and_gpu_round_robin(registry, patch_completion_async):
    engine = AnalysisWorkflowEngine(registry, max_concurrency=4, gpu_cores=3)
    jobs = [
        AnalysisJob(analysis_type=AnalysisType.CAPTIONS, base64_image="AAA"),
        AnalysisJob(analysis_type=AnalysisType.OBJECTS, base64_image="BBB"),
        AnalysisJob(analysis_type=AnalysisType.CAPTIONS, base64_image="CCC"),
        AnalysisJob(analysis_type=AnalysisType.OBJECTS, base64_image="DDD"),
    ]
    res = await engine.run_batch(jobs)
    assert len(res) == 4
    assert all(r.success for r in res)
    # GPU ids 0,1,2,0 round-robin
    assert [r.gpu_id for r in res] == [0, 1, 2, 0]


@pytest.mark.asyncio
async def test_parallelism_respected(registry, patch_completion_async):
    engine = AnalysisWorkflowEngine(registry, max_concurrency=2)
    jobs = [AnalysisJob(analysis_type=AnalysisType.CAPTIONS, base64_image="A") for _ in range(6)]
    await engine.run_batch(jobs)
    # ensure observed parallelism does not exceed semaphore
    assert patch_completion_async.max_parallel["max"] <= 2


@pytest.mark.asyncio
async def test_dynamic_params_applied(registry, patch_completion_async):
    engine = AnalysisWorkflowEngine(registry, max_concurrency=2)
    jobs = [AnalysisJob(analysis_type=AnalysisType.CAPTIONS, base64_image="A")]
    await engine.run_batch(jobs)
    # last call args temperature should be bumped to >= 0.2 for descriptive types
    last = patch_completion_async.calls[-1]
    assert float(last.get("temperature", 0.0)) >= 0.2


@pytest.mark.asyncio
async def test_timeout_handling(registry, monkeypatch):
    # Patch completion to sleep long enough to trigger timeout
    async def slow_stub(call_args: dict[str, Any]):
        await asyncio.sleep(0.2)
        return {"choices": [{"message": {"content": "late"}}]}

    import app.services.analysis_engine as engine_mod

    monkeypatch.setattr(engine_mod, "completion_async", slow_stub)

    engine = AnalysisWorkflowEngine(registry, max_concurrency=1, timeout_seconds=0.05)
    jobs = [AnalysisJob(analysis_type=AnalysisType.OBJECTS, base64_image="A")]
    res = await engine.run_batch(jobs)
    assert not res[0].success
    assert "timeout" in (res[0].error or "")


@dataclass
class DummyQA:
    async def run_sequential(self, request):  # type: ignore[no-untyped-def]
        # Return deterministic structure
        return types.SimpleNamespace(
            aggregate_confidence=0.77,
            results=[
                types.SimpleNamespace(
                    stage="structural",
                    response=types.SimpleNamespace(confidence=0.8),
                ),
                types.SimpleNamespace(
                    stage="content_quality",
                    response=types.SimpleNamespace(confidence=0.75),
                ),
            ],
        )


@pytest.mark.asyncio
async def test_qa_integration(registry, monkeypatch):
    # Fast stub for completion
    async def ok_stub(call_args: dict[str, Any]):
        return {"choices": [{"message": {"content": "ok"}}]}

    import app.services.analysis_engine as engine_mod

    monkeypatch.setattr(engine_mod, "completion_async", ok_stub)

    engine = AnalysisWorkflowEngine(registry, max_concurrency=1, qa_orchestrator=DummyQA())
    jobs = [AnalysisJob(analysis_type=AnalysisType.OBJECTS, base64_image="A")]
    res = await engine.run_batch(jobs)
    assert res[0].qa is not None
    assert res[0].qa.get("aggregate_confidence") == 0.77
    assert len(res[0].qa.get("stages", [])) == 2
