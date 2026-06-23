from dataclasses import dataclass, field
from typing import Literal
from uuid import uuid4


ModuleName = Literal[
    "orientation",
    "group_dna",
    "competency_model",
    "feedback_coaching",
    "talent_mobility",
    "regional_rollout",
    "executive_recommendation",
]


@dataclass
class SessionState:
    session_id: str
    current_module: ModuleName = "orientation"
    completed_deliverables: list[str] = field(default_factory=list)
    missing_deliverables: list[str] = field(
        default_factory=lambda: [
            "group_dna",
            "competency_model",
            "360_feedback_plan",
            "coaching_program",
            "talent_mobility_plan",
            "regional_rollout_plan",
            "measurement_plan",
        ]
    )
    user_confidence: str = "unknown"
    stuck_counter: int = 0
    relationship_tone: str = "supportive_but_direct"
    turns: list[dict[str, str]] = field(default_factory=list)


class MemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def create_session(self) -> SessionState:
        session = SessionState(session_id=str(uuid4()))
        self._sessions[session.session_id] = session
        return session

    def load(self, session_id: str | None) -> SessionState:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session()

    def update(
        self,
        state: SessionState,
        user_message: str,
        assistant_message: str,
        supervisor_signal: dict[str, object],
    ) -> SessionState:
        state.turns.append({"user": user_message, "assistant": assistant_message})
        state.turns = state.turns[-8:]

        detected_module = supervisor_signal.get("module")
        if isinstance(detected_module, str) and detected_module:
            state.current_module = detected_module  # type: ignore[assignment]

        completed = supervisor_signal.get("completed_deliverables", [])
        if isinstance(completed, list):
            for item in completed:
                if isinstance(item, str) and item not in state.completed_deliverables:
                    state.completed_deliverables.append(item)
                if item in state.missing_deliverables:
                    state.missing_deliverables.remove(item)

        if supervisor_signal.get("stuck"):
            state.stuck_counter += 1
            state.user_confidence = "low"
        elif user_message.strip():
            state.stuck_counter = max(0, state.stuck_counter - 1)
            state.user_confidence = "medium"

        self._sessions[state.session_id] = state
        return state
