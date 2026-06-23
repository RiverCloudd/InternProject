from .agent_loader import AgentModule
from .llm_client import BaseLLMClient
from .prompt_builder import PromptBuilder


class BaseAgent:
    def __init__(
        self,
        module: AgentModule,
        prompt_builder: PromptBuilder,
        llm_client: BaseLLMClient,
        tool_catalog: dict[str, object],
    ) -> None:
        self.module = module
        self.agent_id = module.agent_id
        self.profile = module.profile
        self.system_prompt = module.system_prompt
        self.skills = module.skills
        self.tasks = module.tasks
        self.memory_schema = module.memory_schema
        self.handoff_rules = module.handoff_rules
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.tool_catalog = tool_catalog

    def respond(
        self,
        user_message: str,
        simulation_context: list[dict],
        memory_summary: dict[str, object],
        shared_state: dict[str, object],
        supervisor_signal: dict[str, object],
        consultations: list[dict[str, str]] | None = None,
    ) -> str:
        prompt = self._build_prompt(
            mode="direct_or_consult",
            user_message=user_message,
            simulation_context=simulation_context,
            memory_summary=memory_summary,
            shared_state=shared_state,
            supervisor_signal=supervisor_signal,
            consultations=consultations or [],
        )
        return self.llm_client.generate(prompt)

    def private_consult(
        self,
        user_message: str,
        primary_agent_id: str,
        shared_state: dict[str, object],
        simulation_context: list[dict],
    ) -> str:
        prompt = self._build_prompt(
            mode="private_consult",
            user_message=user_message,
            simulation_context=simulation_context,
            memory_summary={},
            shared_state=shared_state,
            supervisor_signal={"primary_agent_id": primary_agent_id},
            consultations=[],
        )
        return self.llm_client.generate(prompt)

    def respond_as_panelist(
        self,
        user_message: str,
        simulation_context: list[dict],
        shared_state: dict[str, object],
    ) -> str:
        prompt = self._build_prompt(
            mode="panel",
            user_message=user_message,
            simulation_context=simulation_context,
            memory_summary={},
            shared_state=shared_state,
            supervisor_signal={},
            consultations=[],
        )
        return self.llm_client.generate(prompt)

    def challenge(self, proposal: str, shared_state: dict[str, object]) -> str:
        prompt = self._build_prompt(
            mode="challenge",
            user_message=proposal,
            simulation_context=[],
            memory_summary={},
            shared_state=shared_state,
            supervisor_signal={},
            consultations=[],
        )
        return self.llm_client.generate(prompt)

    def _build_prompt(
        self,
        mode: str,
        user_message: str,
        simulation_context: list[dict],
        memory_summary: dict[str, object],
        shared_state: dict[str, object],
        supervisor_signal: dict[str, object],
        consultations: list[dict[str, str]],
    ) -> str:
        enriched_signal = {
            **supervisor_signal,
            "mode": mode,
            "user_message": user_message,
            "shared_state": shared_state,
            "consultations": consultations,
        }
        return self.prompt_builder.build(
            agent=self.module,
            retrieved_context=simulation_context,
            memory_summary=memory_summary,
            supervisor_signal=enriched_signal,
            tool_catalog=self.tool_catalog,
        )
