from fastapi import APIRouter

from .schemas import ChatRequest, ChatResponse, LegacyChatRequest
from ..orchestrator import MultiAgentOrchestrator


def create_router(orchestrator: MultiAgentOrchestrator) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.get("/agents")
    def agents() -> dict[str, object]:
        return orchestrator.list_agents()

    @router.get("/api/agents")
    def agents_compat() -> dict[str, object]:
        data = orchestrator.list_agents()
        return {"default_agent_id": "gucci_group_chro", **data}

    @router.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> dict[str, object]:
        return orchestrator.handle_user_message(
            session_id=request.session_id,
            user_message=request.message,
            target_agent_id=request.target_agent_id,
            requested_mode=request.mode,
        )

    @router.post("/chat/{agent_id}")
    def chat_agent_compat(agent_id: str, request: LegacyChatRequest) -> dict[str, object]:
        session_id = request.session_id or "default-session"
        result = orchestrator.handle_user_message(
            session_id=session_id,
            user_message=request.message,
            target_agent_id=agent_id,
            requested_mode="auto",
        )
        return {
            "agent_id": result["active_agent"],
            "agent_name": result["active_agent"],
            "session_id": session_id,
            "assistant_message": result["response"],
            "state": {
                "session_id": session_id,
                "current_module": result["supervisor_signal"].get("module", "orientation"),
                "completed_deliverables": [],
                "missing_deliverables": result["blackboard"].get("missing_outputs", []),
                "user_confidence": "medium",
                "stuck_counter": 0,
                "relationship_tone": "supportive_but_direct",
            },
            "context": result["retrieved_context"],
            "rag_context": result["retrieved_context"],
            "safety_flags": {flag: True for flag in result["safety_flags"]},
            "supervisor_signal": result["supervisor_signal"],
            "tool_suggestions": [],
            "collaboration": {
                "primary_agent_id": result["active_agent"],
                "collaborators": result["supporting_agents"],
                "notes": [
                    {
                        "agent_id": agent_id,
                        "role": agent_id,
                        "advisory_note": "Supporting agent consulted through orchestrator.",
                    }
                    for agent_id in result["supporting_agents"]
                ],
            },
            "system_prompt": None,
        }

    @router.post("/api/chat")
    def chat_default_compat(request: LegacyChatRequest) -> dict[str, object]:
        return chat_agent_compat("gucci_group_chro", request)

    return router
