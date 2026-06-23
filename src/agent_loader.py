from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AgentModule:
    agent_id: str
    base_path: Path
    profile: dict[str, Any]
    system_prompt: str
    skills: dict[str, Any]
    tasks: dict[str, Any]
    memory_schema: dict[str, Any]
    handoff_rules: dict[str, Any]
    examples: str

    @property
    def display_name(self) -> str:
        return str(self.profile.get("name", self.agent_id))

    @property
    def role(self) -> str:
        return str(self.profile.get("role", self.agent_id))


@dataclass(frozen=True)
class SharedResources:
    simulation_context: str
    common_guardrails: str
    supervisor_rules: dict[str, Any]
    tool_catalog: dict[str, Any]
    base_prompt_template: str


class AgentLoader:
    REQUIRED_FILES = [
        "profile.yaml",
        "system_prompt.md",
        "skills.yaml",
        "tasks.yaml",
        "memory_schema.yaml",
        "handoff_rules.yaml",
        "examples.md",
    ]

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.agents_dir = self.base_dir / "agents"
        self.shared_dir = self.base_dir / "shared"

    def list_agents(self) -> list[dict[str, str]]:
        agents: list[dict[str, str]] = []
        for path in sorted(self.agents_dir.iterdir()):
            if not path.is_dir():
                continue
            try:
                agent = self.load(path.name)
            except (FileNotFoundError, ValueError):
                continue
            agents.append(
                {
                    "agent_id": agent.agent_id,
                    "name": agent.display_name,
                    "role": agent.role,
                }
            )
        return agents

    def load(self, agent_id: str) -> AgentModule:
        if agent_id not in {path.name for path in self.agents_dir.iterdir() if path.is_dir()}:
            raise ValueError(f"Unknown agent_id: {agent_id}")

        base_path = self.agents_dir / agent_id
        missing = [filename for filename in self.REQUIRED_FILES if not (base_path / filename).exists()]
        if missing:
            raise FileNotFoundError(f"Agent {agent_id} is missing files: {missing}")

        profile = self._load_yaml(base_path / "profile.yaml")
        persona_id = profile.get("persona_id")
        if persona_id != agent_id:
            raise ValueError(f"profile.yaml persona_id must match folder name for {agent_id}.")

        return AgentModule(
            agent_id=agent_id,
            base_path=base_path,
            profile=profile,
            system_prompt=self._load_text(base_path / "system_prompt.md"),
            skills=self._load_yaml(base_path / "skills.yaml"),
            tasks=self._load_yaml(base_path / "tasks.yaml"),
            memory_schema=self._load_yaml(base_path / "memory_schema.yaml"),
            handoff_rules=self._load_yaml(base_path / "handoff_rules.yaml"),
            examples=self._load_text(base_path / "examples.md"),
        )

    def load_shared(self) -> SharedResources:
        return SharedResources(
            simulation_context=self._load_text(self.shared_dir / "simulation_context.md"),
            common_guardrails=self._load_text(self.shared_dir / "common_guardrails.md"),
            supervisor_rules=self._load_yaml(self.shared_dir / "supervisor_rules.yaml"),
            tool_catalog=self._load_yaml(self.shared_dir / "tool_catalog.yaml"),
            base_prompt_template=self._load_text(self.shared_dir / "base_prompt_template.md"),
        )

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            raise ValueError(f"{path} must contain a YAML mapping.")
        return data

    def _load_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")
