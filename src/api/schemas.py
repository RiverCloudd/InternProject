from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(default="default-session", min_length=1)
    message: str = Field(min_length=1, max_length=4000)
    target_agent_id: str | None = None
    mode: str = "auto"


class LegacyChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class RetrievedContextItem(BaseModel):
    document_id: str | None = None
    chunk_id: str | None = None
    score: float
    module_id: str | None = None
    source_path: str | None = None


class ChatResponse(BaseModel):
    response: str
    active_agent: str
    supporting_agents: list[str]
    interaction_mode: str
    intent: str | None
    retrieved_context: list[RetrievedContextItem]
    supervisor_signal: dict[str, Any]
    safety_flags: list[str]
    llm_provider: str
    blackboard: dict[str, Any]
    message_bus: list[dict[str, Any]]
    retrieved_context_full: list[dict[str, Any]] = []


class LegacyChatResponse(BaseModel):
    agent_id: str
    agent_name: str
    session_id: str
    assistant_message: str
    state: dict[str, object]
    context: list[dict[str, object]]
    rag_context: list[dict[str, object]]
    safety_flags: dict[str, bool]
    supervisor_signal: dict[str, object]
    tool_suggestions: list[str]
    collaboration: dict[str, object]
    system_prompt: str | None = None
