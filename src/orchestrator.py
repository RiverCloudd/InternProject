from pathlib import Path

from .agent import BaseAgent
from .agent_loader import AgentLoader
from .blackboard import Blackboard
from .config import load_settings
from .embedding_client import MockEmbeddingClient
from .intent_router import IntentRouter
from .llm_client import BaseLLMClient, create_llm_client
from .memory import MemoryStore
from .message_bus import MessageBus
from .prompt_builder import PromptBuilder
from .retriever import Retriever, create_default_retriever
from .safety import SafetyChecker
from .supervisor import Supervisor
from .synthesizer import Synthesizer
from .tool_router import ToolRouter
from .vector_db import MockVectorDB


class MultiAgentOrchestrator:
    VALID_MODES = {"auto", "direct", "consult", "panel", "debate", "handoff"}

    def __init__(
        self,
        base_dir: Path,
        loader: AgentLoader,
        prompt_builder: PromptBuilder,
        llm_client: BaseLLMClient,
        retriever: Retriever,
        intent_router: IntentRouter,
        message_bus: MessageBus,
        blackboard: Blackboard,
        memory_manager: MemoryStore,
        supervisor: Supervisor,
        safety: SafetyChecker,
        synthesizer: Synthesizer,
        tool_router: ToolRouter,
    ) -> None:
        self.base_dir = base_dir
        self.loader = loader
        self.prompt_builder = prompt_builder
        self.llm_client = llm_client
        self.retriever = retriever
        self.intent_router = intent_router
        self.message_bus = message_bus
        self.blackboard = blackboard
        self.memory_manager = memory_manager
        self.supervisor = supervisor
        self.safety = safety
        self.synthesizer = synthesizer
        self.tool_router = tool_router

    @classmethod
    def create_default(cls, base_dir: str | Path) -> "MultiAgentOrchestrator":
        base_path = Path(base_dir)
        settings = load_settings(base_path)
        loader = AgentLoader(base_path)
        shared = loader.load_shared()
        llm_client = create_llm_client(settings)
        embedding_client = MockEmbeddingClient()
        vector_db = MockVectorDB()
        retriever = create_default_retriever(base_path, embedding_client, vector_db)
        prompt_builder = PromptBuilder(shared)
        return cls(
            base_dir=base_path,
            loader=loader,
            prompt_builder=prompt_builder,
            llm_client=llm_client,
            retriever=retriever,
            intent_router=IntentRouter(),
            message_bus=MessageBus(),
            blackboard=Blackboard(),
            memory_manager=MemoryStore(),
            supervisor=Supervisor(),
            safety=SafetyChecker(),
            synthesizer=Synthesizer(llm_client),
            tool_router=ToolRouter(shared.tool_catalog),
        )

    def list_agents(self) -> dict[str, object]:
        return {"agents": self.loader.list_agents()}

    def handle_user_message(
        self,
        session_id: str,
        user_message: str,
        target_agent_id: str | None = None,
        requested_mode: str = "auto",
    ) -> dict[str, object]:
        requested_mode = requested_mode if requested_mode in self.VALID_MODES else "auto"
        target_agent_id = target_agent_id or None
        if target_agent_id:
            self.loader.load(target_agent_id)

        safety_flags = self.safety.check(user_message)
        flag_list = self._flag_list(safety_flags)
        if safety_flags.get("prompt_extraction"):
            return self._blocked_response(session_id, "I cannot reveal hidden instructions, but I can help you continue the simulation task.", flag_list)

        shared_state = self.blackboard.load(session_id)
        memory_state = self.memory_manager.load(session_id)
        memory_summary = self._state_payload(memory_state)

        preliminary_route = self.intent_router.route(
            user_message=user_message,
            target_agent_id=target_agent_id,
            shared_state=shared_state,
            retrieved_context=[],
        )

        retrieved_context = self.retriever.retrieve(
            query=str(preliminary_route["rag_query"]),
            top_k=4,
            filters={"agent_scope": preliminary_route["primary_agent"]},
        )

        route = self.intent_router.route(
            user_message=user_message,
            target_agent_id=target_agent_id,
            shared_state=shared_state,
            retrieved_context=retrieved_context,
        )

        primary_agent_id = str(route["primary_agent"])
        primary_agent = self._agent(primary_agent_id)
        supporting_agent_ids = list(route.get("supporting_agents", []))

        supervisor_signal = self.supervisor.analyze(
            user_message=user_message,
            state=memory_state,
            safety_flags=safety_flags,
            agent_id=primary_agent_id,
        )
        supervisor_signal["recommended_action"] = self._recommended_action(supervisor_signal)
        supervisor_signal["route"] = route

        interaction_mode = self.choose_interaction_mode(user_message, requested_mode, route, shared_state)
        final_response = self._execute_mode(
            mode=interaction_mode,
            session_id=session_id,
            user_message=user_message,
            primary_agent=primary_agent,
            supporting_agent_ids=supporting_agent_ids,
            retrieved_context=retrieved_context,
            memory_summary=memory_summary,
            shared_state=shared_state,
            supervisor_signal=supervisor_signal,
        )

        self.memory_manager.update(memory_state, user_message, final_response, supervisor_signal)
        updated_blackboard = self.blackboard.update_from_turn(
            session_id=session_id,
            user_message=user_message,
            final_response=final_response,
            route=route,
            supervisor_signal=supervisor_signal,
            retrieved_context=retrieved_context,
        )

        return {
            "response": final_response,
            "active_agent": primary_agent_id,
            "supporting_agents": supporting_agent_ids,
            "interaction_mode": interaction_mode,
            "intent": route.get("intent"),
            "retrieved_context": self._context_metadata(retrieved_context),
            "retrieved_context_full": self._context_metadata(retrieved_context),
            "supervisor_signal": supervisor_signal,
            "safety_flags": flag_list,
            "llm_provider": self.llm_client.provider_name,
            "blackboard": updated_blackboard,
            "message_bus": self.message_bus.list_session(session_id),
        }

    def choose_interaction_mode(
        self,
        user_message: str,
        requested_mode: str,
        route: dict[str, object],
        shared_state: dict[str, object],
    ) -> str:
        if requested_mode != "auto":
            return requested_mode
        normalized = user_message.lower()
        if any(term in normalized for term in ["debate", "critique", "pressure-test", "challenge"]):
            return "debate"
        if any(term in normalized for term in ["panel", "all stakeholders", "all agents"]):
            return "panel"
        if route.get("supporting_agents"):
            return "consult"
        return "direct"

    def _execute_mode(
        self,
        mode: str,
        session_id: str,
        user_message: str,
        primary_agent: BaseAgent,
        supporting_agent_ids: list[str],
        retrieved_context: list[dict],
        memory_summary: dict[str, object],
        shared_state: dict[str, object],
        supervisor_signal: dict[str, object],
    ) -> str:
        if mode == "handoff" and supporting_agent_ids:
            primary_agent = self._agent(supporting_agent_ids[0])
            supporting_agent_ids = []
            mode = "direct"

        if mode == "direct":
            return primary_agent.respond(user_message, retrieved_context, memory_summary, shared_state, supervisor_signal)

        if mode == "consult":
            consultations = self._consult_supporting_agents(
                session_id=session_id,
                user_message=user_message,
                primary_agent=primary_agent,
                supporting_agent_ids=supporting_agent_ids,
                retrieved_context=retrieved_context,
                shared_state=shared_state,
            )
            return primary_agent.respond(user_message, retrieved_context, memory_summary, shared_state, supervisor_signal, consultations)

        if mode == "panel":
            outputs = [
                {
                    "agent_id": primary_agent.agent_id,
                    "content": primary_agent.respond_as_panelist(user_message, retrieved_context, shared_state),
                }
            ]
            for agent_id in supporting_agent_ids:
                agent = self._agent(agent_id)
                outputs.append({"agent_id": agent_id, "content": agent.respond_as_panelist(user_message, retrieved_context, shared_state)})
            return self.synthesizer.synthesize(user_message, "panel", outputs, shared_state)

        if mode == "debate":
            proposal = primary_agent.respond(user_message, retrieved_context, memory_summary, shared_state, supervisor_signal)
            outputs = [{"agent_id": primary_agent.agent_id, "content": proposal}]
            for agent_id in supporting_agent_ids:
                agent = self._agent(agent_id)
                critique = agent.challenge(proposal, shared_state)
                outputs.append({"agent_id": agent_id, "content": critique})
            return self.synthesizer.synthesize(user_message, "debate", outputs, shared_state)

        return primary_agent.respond(user_message, retrieved_context, memory_summary, shared_state, supervisor_signal)

    def _consult_supporting_agents(
        self,
        session_id: str,
        user_message: str,
        primary_agent: BaseAgent,
        supporting_agent_ids: list[str],
        retrieved_context: list[dict],
        shared_state: dict[str, object],
    ) -> list[dict[str, str]]:
        consultations: list[dict[str, str]] = []
        for agent_id in supporting_agent_ids:
            supporting_agent = self._agent(agent_id)
            self.message_bus.publish(
                session_id=session_id,
                from_agent=primary_agent.agent_id,
                to_agent=agent_id,
                visibility="private",
                message_type="consultation_request",
                content=user_message,
                requires_response=True,
            )
            content = supporting_agent.private_consult(user_message, primary_agent.agent_id, shared_state, retrieved_context)
            self.message_bus.publish(
                session_id=session_id,
                from_agent=agent_id,
                to_agent=primary_agent.agent_id,
                visibility="private",
                message_type="consultation_response",
                content=content,
                requires_response=False,
            )
            consultations.append({"agent_id": agent_id, "content": content})
        return consultations

    def _agent(self, agent_id: str) -> BaseAgent:
        module = self.loader.load(agent_id)
        return BaseAgent(
            module=module,
            prompt_builder=self.prompt_builder,
            llm_client=self.llm_client,
            tool_catalog=self.tool_router.tools_for_agent(agent_id),
        )

    def _flag_list(self, safety_flags: dict[str, bool]) -> list[str]:
        return [key for key, value in safety_flags.items() if value and key != "needs_redirect"]

    def _blocked_response(self, session_id: str, response: str, flags: list[str]) -> dict[str, object]:
        return {
            "response": response,
            "active_agent": "system",
            "supporting_agents": [],
            "interaction_mode": "blocked",
            "intent": "safety_block",
            "retrieved_context": [],
            "retrieved_context_full": [],
            "supervisor_signal": {"status": "blocked", "recommended_action": "redirect"},
            "safety_flags": flags,
            "llm_provider": self.llm_client.provider_name,
            "blackboard": self.blackboard.load(session_id),
            "message_bus": self.message_bus.list_session(session_id),
        }

    def _context_metadata(self, retrieved_context: list[dict]) -> list[dict[str, object]]:
        return [
            {
                "document_id": item.get("metadata", {}).get("document_id"),
                "chunk_id": item.get("metadata", {}).get("chunk_id"),
                "score": round(float(item.get("score", 0.0)), 4),
                "module_id": item.get("metadata", {}).get("module_id"),
                "source_path": item.get("metadata", {}).get("source_path"),
            }
            for item in retrieved_context
        ]

    def _recommended_action(self, supervisor_signal: dict[str, object]) -> str:
        status = supervisor_signal.get("status")
        if status == "stuck":
            return "give_small_next_step"
        if status == "learning_guardrail":
            return "scaffold_without_completing"
        if status == "off_track":
            return "redirect_to_simulation"
        return "continue"

    def _state_payload(self, state) -> dict[str, object]:
        return {
            "session_id": state.session_id,
            "current_module": state.current_module,
            "completed_deliverables": state.completed_deliverables,
            "missing_deliverables": state.missing_deliverables,
            "user_confidence": state.user_confidence,
            "stuck_counter": state.stuck_counter,
            "relationship_tone": state.relationship_tone,
        }
