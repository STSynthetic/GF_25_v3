from __future__ import annotations

from typing import Any

from app.agents.base import Agent, AgentRequest, AgentResponse
from app.llm.litellm_config import completion


class ContentQualityQAAgent(Agent):
    async def run(
        self, request: AgentRequest
    ) -> AgentResponse:  # pragma: no cover - exercised in tests
        resp: dict[str, Any] = completion(
            request.prompt,
            model_cfg={"model": "ollama/qwen2.5vl:32b", "temperature": 0.1, **self.model_cfg},
        )
        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        return AgentResponse(content=content, confidence=0.5, raw=resp)
