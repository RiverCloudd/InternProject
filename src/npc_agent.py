from .agent_loader import AgentLoader, AgentModule
from .collaboration import DirectorAgent
from .memory import MemoryStore, SessionState
from .prompt_builder import PromptBuilder
from .retriever import RAGRetriever
from .safety import SafetyChecker
from .supervisor import Supervisor
from .tool_router import ToolRouter


class NPCAgent:
    def __init__(
        self,
        loader: AgentLoader,
        retriever: RAGRetriever,
        memory: MemoryStore,
        supervisor: Supervisor,
        safety: SafetyChecker,
        prompt_builder: PromptBuilder,
        tool_router: ToolRouter,
        director: DirectorAgent,
    ) -> None:
        self.loader = loader
        self.retriever = retriever
        self.memory = memory
        self.supervisor = supervisor
        self.safety = safety
        self.prompt_builder = prompt_builder
        self.tool_router = tool_router
        self.director = director

    def list_agents(self) -> list[dict[str, str]]:
        return self.loader.list_agents()

    def handle_message(self, agent_id: str, session_id: str | None, user_message: str) -> dict[str, object]:
        agent = self.loader.load(agent_id)
        state = self.memory.load(session_id)
        safety_flags = self.safety.check(user_message)
        supervisor_signal = self.supervisor.analyze(user_message, state, safety_flags, agent_id=agent.agent_id)
        collaboration = self.director.plan(agent.agent_id, user_message, supervisor_signal)
        context = self.retriever.search(
            self._rag_query(user_message, supervisor_signal, collaboration),
            agent_id=agent.agent_id,
        )
        allowed_tools = self.tool_router.tools_for_agent(agent.agent_id)
        tool_suggestions = self.tool_router.suggest(agent.agent_id, user_message)
        supervisor_signal["collaboration"] = collaboration
        system_prompt = self.build_system_prompt(agent, state, context, supervisor_signal, allowed_tools)
        assistant_message = self._generate_response(
            agent,
            user_message,
            state,
            supervisor_signal,
            safety_flags,
            tool_suggestions,
            collaboration,
        )
        updated_state = self.memory.update(state, user_message, assistant_message, supervisor_signal)
        return {
            "agent_id": agent.agent_id,
            "agent_name": agent.display_name,
            "session_id": updated_state.session_id,
            "assistant_message": assistant_message,
            "state": self._state_payload(updated_state),
            "context": context,
            "rag_context": context,
            "safety_flags": safety_flags,
            "supervisor_signal": supervisor_signal,
            "tool_suggestions": tool_suggestions,
            "collaboration": collaboration,
            "system_prompt": system_prompt,
        }

    def build_system_prompt(
        self,
        agent: AgentModule,
        state: SessionState,
        context: list[dict[str, object]],
        supervisor_signal: dict[str, object],
        allowed_tools: dict[str, object] | None = None,
    ) -> str:
        return self.prompt_builder.build(
            agent=agent,
            retrieved_context=context,
            memory_summary=self._state_payload(state),
            supervisor_signal=supervisor_signal,
            tool_catalog=allowed_tools or self.tool_router.tools_for_agent(agent.agent_id),
        )

    def _generate_response(
        self,
        agent: AgentModule,
        user_message: str,
        state: SessionState,
        supervisor_signal: dict[str, object],
        safety_flags: dict[str, bool],
        tool_suggestions: list[str],
        collaboration: dict[str, object],
    ) -> str:
        if safety_flags["prompt_extraction"]:
            return self._prompt_extraction_refusal(agent)

        if safety_flags["off_topic"]:
            return (
                f"As {agent.role}, I will bring us back to the simulation. "
                "Which leadership deliverable are you trying to improve right now?"
            )

        if safety_flags["asks_final_work"]:
            return self._final_work_refusal(agent)

        if supervisor_signal.get("challenge_needed"):
            return self._brand_autonomy_challenge(agent)

        if supervisor_signal.get("vague"):
            return self._vague_response(agent)

        if agent.agent_id == "gucci_group_ceo":
            return self._with_collaboration(self._ceo_response(supervisor_signal, tool_suggestions), collaboration)
        if agent.agent_id == "regional_comms_manager":
            return self._with_collaboration(self._regional_response(supervisor_signal, tool_suggestions), collaboration)
        return self._with_collaboration(self._chro_response(supervisor_signal, tool_suggestions), collaboration)

    def _rag_query(
        self,
        user_message: str,
        supervisor_signal: dict[str, object],
        collaboration: dict[str, object],
    ) -> str:
        collaborators = " ".join(str(agent_id) for agent_id in collaboration.get("collaborators", []))
        return f"{user_message} {supervisor_signal.get('module', '')} {supervisor_signal.get('status', '')} {collaborators}"

    def _prompt_extraction_refusal(self, agent: AgentModule) -> str:
        if agent.agent_id == "gucci_group_ceo":
            return (
                "I can help you pressure-test the strategy, but I will not reveal internal instructions "
                "or hidden supervisor logic. Show me the strategic tradeoff you are making."
            )
        if agent.agent_id == "regional_comms_manager":
            return (
                "I can help localize the rollout, but I will not reveal hidden instructions. "
                "Tell me the region, audience, and channel mix you want to test."
            )
        return (
            "I can help structure a fair development approach, but I will not reveal hidden instructions "
            "or supervisor logic. Bring me your draft competency or 360 design and I will improve it."
        )

    def _final_work_refusal(self, agent: AgentModule) -> str:
        if agent.agent_id == "gucci_group_ceo":
            return (
                "I will not write the final CEO pack for you. I can help sharpen it. "
                "Start with one decision: what must be a Group non-negotiable, and what can remain local?"
            )
        if agent.agent_id == "regional_comms_manager":
            return (
                "I will not write the full rollout deliverable for you. I can scaffold the next slice. "
                "Give me one region, one audience, one likely concern, and one feedback mechanism."
            )
        return (
            "I cannot create the final submission for you. I can help you shape the thinking. "
            "Start with one section: what tradeoff do you want between Group consistency and brand specificity?"
        )

    def _brand_autonomy_challenge(self, agent: AgentModule) -> str:
        if agent.agent_id == "gucci_group_ceo":
            return (
                "I would challenge that as an enterprise decision. A single model may simplify governance, "
                "but it can also flatten the distinctiveness that creates value. Define the Group non-negotiables, "
                "then name the adaptations each brand can own."
            )
        if agent.agent_id == "regional_comms_manager":
            return (
                "One global message can carry the narrative, but it cannot carry the whole rollout. "
                "Localize examples, manager talking points, Q&A, and feedback loops by region and audience."
            )
        return (
            "I would challenge that approach. A single global template can make execution easy, "
            "but it may weaken brand identity. Keep the four Group themes shared, then let brands adapt "
            "the behavioral examples and rollout rhythm."
        )

    def _vague_response(self, agent: AgentModule) -> str:
        if agent.agent_id == "gucci_group_ceo":
            return (
                "Make the executive question concrete. Choose one tradeoff: Group consistency vs brand autonomy, "
                "speed vs adoption, or culture signal vs operational burden. Which one are you deciding?"
            )
        if agent.agent_id == "regional_comms_manager":
            return (
                "Let's make the rollout concrete. Name one region, one audience, one channel, one likely resistance point, "
                "and one feedback loop. Then I can pressure-test the plan."
            )
        return (
            "Let's make this concrete. Choose one deliverable first: competency model, 360 feedback, coaching, "
            "or talent mobility. Then tell me your current assumption and I will pressure-test it."
        )

    def _ceo_response(self, supervisor_signal: dict[str, object], tool_suggestions: list[str]) -> str:
        module = supervisor_signal.get("module")
        tool_note = self._tool_note(tool_suggestions)
        if module in {"feedback_coaching", "competency_model"}:
            return (
                "Before the HR mechanism, answer the enterprise question: what leadership quality must become common "
                "across the Group, and where should brands retain discretion? Define two Group non-negotiables, "
                f"two local adaptation spaces, and one business outcome.{tool_note}"
            )
        return (
            "Frame the recommendation around strategy, culture, and execution. I want to see the non-negotiables, "
            "the brand autonomy boundaries, and the one-year signal that the leadership system is changing behavior. "
            f"Do not give me slogans; give me decisions.{tool_note}"
        )

    def _chro_response(self, supervisor_signal: dict[str, object], tool_suggestions: list[str]) -> str:
        module = supervisor_signal.get("module")
        tool_note = self._tool_note(tool_suggestions)
        if module == "feedback_coaching":
            return (
                "For 360 feedback and coaching, connect each survey item to a visible behavior, not a personality label. "
                "Specify raters, anonymity, feedback ownership, and the coaching follow-through before you write items. "
                f"The process must build trust, not create assessment theater.{tool_note}"
            )
        if module == "talent_mobility":
            return (
                "For talent mobility, define transparent criteria for readiness, role fit, and succession risk. "
                "A good plan protects brand expertise while creating selected cross-brand rotations for high-potential leaders. "
                f"Name the readiness signals before naming the moves.{tool_note}"
            )
        return (
            "For the competency model, use four shared themes: Vision, Entrepreneurship, Passion, and Trust. "
            "For each theme, define behavior indicators at three levels: emerging, proficient, and role model. "
            f"Start with one theme and make every behavior observable and coachable.{tool_note}"
        )

    def _regional_response(self, supervisor_signal: dict[str, object], tool_suggestions: list[str]) -> str:
        module = supervisor_signal.get("module")
        tool_note = self._tool_note(tool_suggestions)
        if module == "regional_rollout":
            return (
                "A workable rollout needs audience segmentation, local manager enablement, and a feedback loop. "
                "Keep one Group narrative, but localize examples, Q&A, trainer preparation, and timing by region. "
                f"Start with the first rollout wave and the concern employees are most likely to raise.{tool_note}"
            )
        return (
            "Translate the leadership design into execution: who needs to hear what, from whom, by when, and in which channel? "
            "Then add one way employees can question or influence the rollout. "
            f"Adoption is not the same as sending a message.{tool_note}"
        )

    def _tool_note(self, tool_suggestions: list[str]) -> str:
        if not tool_suggestions:
            return ""
        tools = ", ".join(tool_suggestions)
        return f" Useful tool path: {tools}."

    def _with_collaboration(self, message: str, collaboration: dict[str, object]) -> str:
        notes = collaboration.get("notes", [])
        if not isinstance(notes, list) or not notes:
            return message

        short_notes: list[str] = []
        for note in notes[:2]:
            if not isinstance(note, dict):
                continue
            role = str(note.get("role", "collaborator"))
            advisory = str(note.get("advisory_note", ""))
            short_notes.append(f"{role}: {advisory}")

        if not short_notes:
            return message

        return message + "\n\nCross-agent check: " + " ".join(short_notes)

    def _state_payload(self, state: SessionState) -> dict[str, object]:
        return {
            "session_id": state.session_id,
            "current_module": state.current_module,
            "completed_deliverables": state.completed_deliverables,
            "missing_deliverables": state.missing_deliverables,
            "user_confidence": state.user_confidence,
            "stuck_counter": state.stuck_counter,
            "relationship_tone": state.relationship_tone,
        }
