from typing import Any

import yaml

from .agent_loader import AgentModule, SharedResources


class PromptBuilder:
    def __init__(self, shared: SharedResources) -> None:
        self.shared = shared

    def build(
        self,
        agent: AgentModule,
        retrieved_context: list[dict[str, object]],
        memory_summary: dict[str, Any],
        supervisor_signal: dict[str, Any],
        tool_catalog: dict[str, Any],
    ) -> str:
        simulation_context = self.shared.simulation_context
        if retrieved_context:
            simulation_context = simulation_context + "\n\n# Retrieved Context\n\n" + self._format_retrieved_context(retrieved_context)

        values = {
            "profile": self._dump(agent.profile),
            "skills": self._dump(agent.skills),
            "tasks": self._dump(agent.tasks),
            "memory_schema": self._dump(agent.memory_schema),
            "handoff_rules": self._dump(agent.handoff_rules),
            "common_guardrails": self.shared.common_guardrails.strip(),
            "system_prompt": agent.system_prompt.strip(),
            "simulation_context": simulation_context.strip(),
            "memory_summary": self._dump(memory_summary),
            "supervisor_signal": self._dump(supervisor_signal),
            "tool_catalog": self._dump(tool_catalog),
        }

        prompt = self.shared.base_prompt_template
        for key, value in values.items():
            prompt = prompt.replace("{{" + key + "}}", value)
        return prompt

    def _dump(self, data: dict[str, Any]) -> str:
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True).strip()

    def _format_retrieved_context(self, chunks: list[dict[str, object]]) -> str:
        formatted: list[str] = []
        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata", {})
            metadata = metadata if isinstance(metadata, dict) else {}
            source = str(chunk.get("source") or metadata.get("source_path") or "unknown")
            content = str(chunk.get("content") or chunk.get("text") or "")
            score = chunk.get("score", "")
            formatted.append(f"[{index}] source: {source} | score: {score}\n{content}")
        return "\n\n".join(formatted)
