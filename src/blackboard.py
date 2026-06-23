from copy import deepcopy


class Blackboard:
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, object]] = {}

    def load(self, session_id: str) -> dict[str, object]:
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "current_module": "orientation",
                "active_deliverable": None,
                "learner_goal": None,
                "completed_outputs": [],
                "missing_outputs": [
                    "group_dna",
                    "competency_matrix",
                    "360_feedback_plan",
                    "coaching_program",
                    "regional_rollout_plan",
                ],
                "key_decisions": [],
                "open_questions": [],
                "risks": [],
                "retrieval_history": [],
            }
        return deepcopy(self._sessions[session_id])

    def update_from_turn(
        self,
        session_id: str,
        user_message: str,
        final_response: str,
        route: dict[str, object],
        supervisor_signal: dict[str, object],
        retrieved_context: list[dict],
    ) -> dict[str, object]:
        state = self.load(session_id)
        state["current_module"] = supervisor_signal.get("module", state.get("current_module"))
        state["active_deliverable"] = route.get("intent", state.get("active_deliverable"))
        state["supervisor_signal"] = supervisor_signal
        state["last_user_message"] = user_message
        state["last_response_summary"] = final_response[:220]
        state["retrieval_history"] = list(state.get("retrieval_history", []))[-4:] + [
            {
                "query": route.get("rag_query", user_message),
                "top_chunks": [item.get("metadata", {}).get("chunk_id") for item in retrieved_context],
            }
        ]
        self._sessions[session_id] = state
        return deepcopy(state)
