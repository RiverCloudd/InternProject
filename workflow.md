# workflow.md

# Multi-Agent AI Co-worker Engine Workflow

This document describes the **source-code workflow** for the Multi-Agent AI Co-worker Engine.

It focuses on how the system should be implemented in code:

- API layer
- Multi-agent orchestration
- Agent loading
- Agent-to-agent interaction
- RAG retrieval
- Vector database
- LLM client abstraction
- Safety checks
- Memory and shared state
- Tool routing
- Response synthesis

This document is intended to guide implementation in a local Python prototype.

---

## 1. Runtime Overview

```text
User / Client
   ↓
FastAPI API Layer
   ↓
Request Validation
   ↓
Safety Check
   ↓
Session State Loader
   ↓
RAG Query Builder
   ↓
Vector DB Retriever
   ↓
Intent Router
   ↓
Interaction Mode Selector
   ↓
Multi-Agent Orchestrator
   ↓
Agent Execution
   ↓
Optional Agent-to-Agent Messages
   ↓
LLM Client
   ↓
Synthesizer
   ↓
Memory + Blackboard Update
   ↓
API Response
```

---

## 2. Core Runtime Principles

The engine should follow these principles:

```text
1. API-first design
2. Agents are loaded from configuration files
3. Agent behavior should not be hard-coded in Python
4. Each agent has its own persona, skills, tasks, memory schema, and handoff rules
5. RAG is used to ground responses in simulation context
6. Vector DB retrieval should be abstracted behind a retriever interface
7. The LLM provider should be abstracted behind an LLM client interface
8. The prototype should run locally without requiring paid API keys
9. Mock components are acceptable if they keep production-compatible interfaces
10. The system should return response metadata for debugging and evaluation
```

---

## 3. Source Code Structure

```text
ai-coworker-engine/
│
├── app.py
├── requirements.txt
├── README.md
├── workflow.md
│
├── agents/
│   ├── gucci_group_ceo/
│   │   ├── profile.yaml
│   │   ├── system_prompt.md
│   │   ├── skills.yaml
│   │   ├── tasks.yaml
│   │   ├── memory_schema.yaml
│   │   ├── handoff_rules.yaml
│   │   └── examples.md
│   │
│   ├── gucci_group_chro/
│   │   ├── profile.yaml
│   │   ├── system_prompt.md
│   │   ├── skills.yaml
│   │   ├── tasks.yaml
│   │   ├── memory_schema.yaml
│   │   ├── handoff_rules.yaml
│   │   └── examples.md
│   │
│   └── regional_comms_manager/
│       ├── profile.yaml
│       ├── system_prompt.md
│       ├── skills.yaml
│       ├── tasks.yaml
│       ├── memory_schema.yaml
│       ├── handoff_rules.yaml
│       └── examples.md
│
├── shared/
│   ├── simulation_context.md
│   ├── common_guardrails.md
│   ├── supervisor_rules.yaml
│   ├── routing_rules.yaml
│   ├── interaction_modes.yaml
│   ├── tool_catalog.yaml
│   └── base_prompt_template.md
│
├── data/
│   ├── gucci_simulation_overview.md
│   ├── module_1_group_dna.md
│   ├── module_2_360_coaching.md
│   ├── module_3_rollout_adoption.md
│   ├── deliverables.md
│   └── common_guardrails.md
│
├── vector_store/
│   ├── faiss.index
│   ├── documents.json
│   └── metadata.json
│
├── src/
│   ├── api/
│   │   ├── schemas.py
│   │   └── routes.py
│   │
│   ├── agent.py
│   ├── agent_loader.py
│   ├── prompt_builder.py
│   ├── orchestrator.py
│   ├── intent_router.py
│   ├── message_bus.py
│   ├── blackboard.py
│   ├── memory.py
│   ├── retriever.py
│   ├── vector_db.py
│   ├── embedding_client.py
│   ├── llm_client.py
│   ├── supervisor.py
│   ├── synthesizer.py
│   ├── safety.py
│   └── tool_router.py
│
└── examples/
    ├── direct_response_example.md
    ├── consult_mode_example.md
    ├── panel_mode_example.md
    ├── debate_mode_example.md
    └── sample_api_request.json
```

---

## 4. API Layer

The prototype should expose a local FastAPI application.

The API does not need to be hosted online.  
It only needs to run locally.

```bash
uvicorn app:app --reload
```

---

## 4.1 Required API Endpoints

### `GET /health`

Used to check whether the service is running.

Response:

```json
{
  "status": "ok"
}
```

---

### `GET /agents`

Returns available agents.

Response:

```json
{
  "agents": [
    {
      "agent_id": "gucci_group_ceo",
      "role": "Gucci Group CEO"
    },
    {
      "agent_id": "gucci_group_chro",
      "role": "Gucci Group CHRO"
    },
    {
      "agent_id": "regional_comms_manager",
      "role": "Employer Branding & Internal Communications Regional Manager"
    }
  ]
}
```

---

### `POST /chat`

Main chat endpoint.

Request:

```json
{
  "session_id": "s001",
  "target_agent_id": "gucci_group_chro",
  "mode": "auto",
  "message": "Can you review my competency framework?"
}
```

Response:

```json
{
  "response": "Your framework is directionally strong, but it needs a clearer distinction between Group-wide non-negotiables and brand-level expression.",
  "active_agent": "gucci_group_chro",
  "supporting_agents": [
    "gucci_group_ceo"
  ],
  "interaction_mode": "consult",
  "intent": "competency_framework",
  "retrieved_context": [
    {
      "document_id": "module_1_group_dna",
      "chunk_id": "module_1_group_dna_002",
      "score": 0.83
    }
  ],
  "supervisor_signal": {
    "status": "on_track",
    "recommended_action": "continue"
  },
  "safety_flags": []
}
```

---

## 4.2 API Schema

File:

```text
src/api/schemas.py
```

Example:

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    session_id: str
    message: str
    target_agent_id: Optional[str] = None
    mode: str = "auto"


class RetrievedContextItem(BaseModel):
    document_id: str
    chunk_id: str
    score: float


class ChatResponse(BaseModel):
    response: str
    active_agent: str
    supporting_agents: List[str]
    interaction_mode: str
    intent: str
    retrieved_context: List[RetrievedContextItem]
    supervisor_signal: Dict[str, Any]
    safety_flags: List[str]
```

---

## 4.3 API Route Example

File:

```text
app.py
```

Example:

```python
from fastapi import FastAPI
from src.api.schemas import ChatRequest
from src.orchestrator import MultiAgentOrchestrator

app = FastAPI(title="Multi-Agent AI Co-worker Engine")

orchestrator = MultiAgentOrchestrator.create_default()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/agents")
def agents():
    return orchestrator.list_agents()


@app.post("/chat")
def chat(request: ChatRequest):
    return orchestrator.handle_user_message(
        session_id=request.session_id,
        user_message=request.message,
        target_agent_id=request.target_agent_id,
        requested_mode=request.mode
    )
```

---

## 5. Main Request Workflow

## Step 1 — Receive API request

The request enters through `POST /chat`.

```python
orchestrator.handle_user_message(
    session_id=request.session_id,
    user_message=request.message,
    target_agent_id=request.target_agent_id,
    requested_mode=request.mode
)
```

---

## Step 2 — Validate and normalize request

The API should validate:

```text
- session_id is present
- message is not empty
- target_agent_id is valid if provided
- mode is one of: auto, direct, consult, panel, debate, handoff
```

---

## Step 3 — Run safety check

File:

```text
src/safety.py
```

Interface:

```python
class SafetyChecker:
    def check(self, user_message: str) -> dict:
        pass
```

Safety checks include:

```text
- Prompt extraction attempt
- Jailbreak attempt
- Request to reveal hidden instructions
- Request for confidential company information
- Request for AI to complete the final deliverable
- Off-topic request
```

Example:

```python
safety_flags = safety.check(user_message)

if safety_flags.get("blocked"):
    return {
        "response": "I can’t help with that, but I can help you continue the simulation task.",
        "active_agent": "system",
        "supporting_agents": [],
        "interaction_mode": "blocked",
        "intent": "safety_block",
        "retrieved_context": [],
        "supervisor_signal": {},
        "safety_flags": safety_flags.get("flags", [])
    }
```

---

## Step 4 — Load session state

The engine loads:

```text
1. Shared blackboard
2. Agent-specific memory
```

```python
shared_state = blackboard.load(session_id)
memory_summary = memory_manager.summarize(session_id)
```

---

## Step 5 — Build RAG query

The RAG query builder can use:

```text
- user message
- target agent
- current module
- active deliverable
- previous open questions
- current intent if available
```

Example:

```python
rag_query = rag_query_builder.build(
    user_message=user_message,
    target_agent_id=target_agent_id,
    shared_state=shared_state
)
```

---

## Step 6 — Retrieve context from Vector DB

The retriever fetches grounded context.

```python
retrieved_context = retriever.retrieve(
    query=rag_query,
    top_k=3,
    filters={
        "agent_scope": target_agent_id,
        "module_id": shared_state.get("current_module")
    }
)
```

---

## Step 7 — Route intent

The intent router chooses the primary agent and supporting agents.

```python
route = intent_router.route(
    user_message=user_message,
    target_agent_id=target_agent_id,
    shared_state=shared_state,
    retrieved_context=retrieved_context
)
```

Example:

```json
{
  "intent": "competency_framework",
  "primary_agent": "gucci_group_chro",
  "supporting_agents": [
    "gucci_group_ceo",
    "regional_comms_manager"
  ]
}
```

---

## Step 8 — Select interaction mode

```python
interaction_mode = orchestrator.choose_interaction_mode(
    user_message=user_message,
    requested_mode=requested_mode,
    route=route,
    shared_state=shared_state
)
```

Supported modes:

```text
direct   → One agent answers directly.
consult  → Primary agent privately consults supporting agents.
panel    → Multiple agents respond as visible stakeholders.
debate   → Agents critique or pressure-test a proposal.
handoff  → Current agent transfers the request to a better-suited agent.
```

---

## Step 9 — Run supervisor analysis

```python
supervisor_signal = supervisor.analyze(
    user_message=user_message,
    shared_state=shared_state,
    memory_summary=memory_summary,
    route=route
)
```

Example:

```json
{
  "status": "stuck",
  "reason": "The learner has asked vague help questions for several turns.",
  "recommended_action": "Give one concrete next step instead of a broad explanation."
}
```

---

## Step 10 — Execute agent workflow

The orchestrator executes one of:

```text
direct
consult
panel
debate
handoff
```

---

## Step 11 — Update memory and blackboard

```python
memory_manager.update(
    session_id=session_id,
    user_message=user_message,
    final_response=final_response,
    route=route,
    supervisor_signal=supervisor_signal
)

blackboard.update_from_turn(
    session_id=session_id,
    user_message=user_message,
    final_response=final_response,
    route=route,
    supervisor_signal=supervisor_signal,
    retrieved_context=retrieved_context
)
```

---

## Step 12 — Return API response

The final response should include both the user-facing answer and debug metadata.

```python
return {
    "response": final_response,
    "active_agent": primary_agent.agent_id,
    "supporting_agents": route.get("supporting_agents", []),
    "interaction_mode": interaction_mode,
    "intent": route.get("intent"),
    "retrieved_context": retrieved_context.metadata(),
    "supervisor_signal": supervisor_signal,
    "safety_flags": safety_flags.get("flags", [])
}
```

---

## 6. Vector Database / RAG Layer

The engine uses RAG to ground agent responses in simulation documents.

Prototype vector database:

```text
FAISS
```

Production alternatives:

```text
Milvus
Pinecone
Weaviate
Qdrant
```

The prototype should use FAISS because it is simple, local, and does not require cloud setup.

---

## 6.1 Indexed Documents

The vector database should index files from:

```text
data/
├── gucci_simulation_overview.md
├── module_1_group_dna.md
├── module_2_360_coaching.md
├── module_3_rollout_adoption.md
├── deliverables.md
└── common_guardrails.md
```

Optional shared files:

```text
shared/
├── simulation_context.md
├── common_guardrails.md
├── routing_rules.yaml
├── tool_catalog.yaml
└── supervisor_rules.yaml
```

---

## 6.2 Chunking Strategy

Each document should be split into chunks before embedding.

Recommended defaults:

```text
chunk_size: 500-800 tokens
chunk_overlap: 80-120 tokens
```

Chunk object:

```json
{
  "chunk_id": "module_1_group_dna_002",
  "document_id": "module_1_group_dna",
  "text": "Module 1 asks the learner to frame the leadership problem and define Group DNA...",
  "metadata": {
    "module_id": "module_1",
    "agent_scope": ["gucci_group_ceo", "gucci_group_chro"],
    "content_type": "module_task",
    "source_path": "data/module_1_group_dna.md"
  }
}
```

---

## 6.3 Metadata Schema

Each chunk should store metadata.

```json
{
  "document_id": "module_1_group_dna",
  "chunk_id": "module_1_group_dna_002",
  "module_id": "module_1",
  "agent_scope": [
    "gucci_group_ceo",
    "gucci_group_chro"
  ],
  "content_type": "module_task",
  "source_path": "data/module_1_group_dna.md"
}
```

Recommended metadata fields:

```text
document_id
chunk_id
module_id
agent_scope
content_type
source_path
token_count
created_at
```

---

## 6.4 Embedding Client

File:

```text
src/embedding_client.py
```

Interface:

```python
class BaseEmbeddingClient:
    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]
```

Mock implementation:

```python
class MockEmbeddingClient(BaseEmbeddingClient):
    def embed_text(self, text: str) -> list[float]:
        return [0.0] * 384
```

Production implementations can use:

```text
OpenAI embeddings
Gemini embeddings
Cohere embeddings
SentenceTransformers
Local embedding models
```

---

## 6.5 Vector DB Interface

File:

```text
src/vector_db.py
```

Interface:

```python
class VectorDB:
    def build_index(self, chunks: list[dict]) -> None:
        raise NotImplementedError

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        filters: dict | None = None
    ) -> list[dict]:
        raise NotImplementedError
```

FAISS implementation should keep the same interface:

```python
class FAISSVectorDB(VectorDB):
    def build_index(self, chunks: list[dict]) -> None:
        pass

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        filters: dict | None = None
    ) -> list[dict]:
        pass
```

Mock implementation:

```python
class MockVectorDB(VectorDB):
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 3,
        filters: dict | None = None
    ) -> list[dict]:
        return [
            {
                "text": "The competency framework includes Vision, Entrepreneurship, Passion, and Trust.",
                "score": 0.9,
                "metadata": {
                    "document_id": "deliverables",
                    "chunk_id": "deliverables_001",
                    "module_id": "module_1",
                    "agent_scope": ["gucci_group_chro"]
                }
            }
        ]
```

---

## 6.6 Retriever Interface

File:

```text
src/retriever.py
```

Interface:

```python
class Retriever:
    def __init__(self, embedding_client, vector_db):
        self.embedding_client = embedding_client
        self.vector_db = vector_db

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        filters: dict | None = None
    ) -> list[dict]:
        query_embedding = self.embedding_client.embed_text(query)

        results = self.vector_db.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )

        return results
```

Returned context format:

```json
[
  {
    "text": "The competency framework includes Vision, Entrepreneurship, Passion, and Trust.",
    "score": 0.91,
    "metadata": {
      "document_id": "deliverables",
      "chunk_id": "deliverables_001",
      "module_id": "module_1",
      "agent_scope": ["gucci_group_chro"]
    }
  }
]
```

---

## 6.7 Retrieval Flow

```text
User message
   ↓
RAG query builder
   ↓
Embedding client
   ↓
Vector DB search
   ↓
Top-k chunks
   ↓
Optional metadata filtering
   ↓
Prompt builder
   ↓
Agent response
```

Default retrieval settings:

```yaml
retrieval:
  vector_db: faiss
  top_k: 3
  chunk_size_tokens: 700
  chunk_overlap_tokens: 100
  metadata_filters:
    - module_id
    - agent_scope
```

---

## 6.8 Latency vs Quality

The engine should support two retrieval modes.

### Fast path

Used for simple or conversational questions.

```text
User message
   ↓
Short memory + persona
   ↓
LLM response
```

Fast path may skip vector search or retrieve only top-1 context.

---

### Deep path

Used for questions about deliverables, module tasks, frameworks, rollout, or evaluation.

```text
User message
   ↓
Query rewrite
   ↓
Vector DB retrieval
   ↓
Top-k chunks
   ↓
Optional reranking
   ↓
Agent response
```

Deep path improves groundedness but increases latency.

---

## 7. LLM Client Layer

The engine should not call any LLM provider directly inside agents.

All LLM calls should go through:

```text
src/llm_client.py
```

Interface:

```python
class BaseLLMClient:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError
```

Mock implementation:

```python
class MockLLMClient(BaseLLMClient):
    def generate(self, prompt: str) -> str:
        return "Mock response from AI co-worker."
```

Production implementations can include:

```text
OpenAI
Claude
Gemini
Mistral
DeepSeek
Local Llama
```

Agent code should call:

```python
assistant_message = llm_client.generate(prompt)
```

---

## 8. Agent Loading Workflow

Each agent is loaded from its folder.

```python
def load_agent(agent_id: str):
    base_path = f"agents/{agent_id}"

    profile = load_yaml(f"{base_path}/profile.yaml")
    system_prompt = load_text(f"{base_path}/system_prompt.md")
    skills = load_yaml(f"{base_path}/skills.yaml")
    tasks = load_yaml(f"{base_path}/tasks.yaml")
    memory_schema = load_yaml(f"{base_path}/memory_schema.yaml")
    handoff_rules = load_yaml(f"{base_path}/handoff_rules.yaml")

    return BaseAgent(
        agent_id=agent_id,
        profile=profile,
        system_prompt=system_prompt,
        skills=skills,
        tasks=tasks,
        memory_schema=memory_schema,
        handoff_rules=handoff_rules
    )
```

---

## 9. Agent Interface

All agents implement the same interface.

```python
class BaseAgent:
    def __init__(
        self,
        agent_id,
        profile,
        system_prompt,
        skills,
        tasks,
        memory_schema,
        handoff_rules,
        llm_client
    ):
        self.agent_id = agent_id
        self.profile = profile
        self.system_prompt = system_prompt
        self.skills = skills
        self.tasks = tasks
        self.memory_schema = memory_schema
        self.handoff_rules = handoff_rules
        self.llm_client = llm_client

    def respond(
        self,
        user_message,
        simulation_context,
        memory_summary,
        shared_state,
        supervisor_signal,
        consultations=None
    ):
        prompt = self.build_prompt(
            mode="direct_or_consult",
            user_message=user_message,
            simulation_context=simulation_context,
            memory_summary=memory_summary,
            shared_state=shared_state,
            supervisor_signal=supervisor_signal,
            consultations=consultations
        )

        return self.llm_client.generate(prompt)

    def private_consult(
        self,
        user_message,
        primary_agent_id,
        shared_state,
        simulation_context
    ):
        prompt = self.build_prompt(
            mode="private_consult",
            user_message=user_message,
            primary_agent_id=primary_agent_id,
            shared_state=shared_state,
            simulation_context=simulation_context
        )

        return self.llm_client.generate(prompt)

    def respond_as_panelist(
        self,
        user_message,
        simulation_context,
        shared_state
    ):
        prompt = self.build_prompt(
            mode="panel",
            user_message=user_message,
            simulation_context=simulation_context,
            shared_state=shared_state
        )

        return self.llm_client.generate(prompt)

    def challenge(self, proposal, shared_state):
        prompt = self.build_prompt(
            mode="challenge",
            proposal=proposal,
            shared_state=shared_state
        )

        return self.llm_client.generate(prompt)
```

---

## 10. Prompt Building Workflow

The prompt builder merges:

```text
- Agent system prompt
- Agent profile
- Agent skills
- Agent tasks
- Retrieved RAG context
- Memory summary
- Shared blackboard state
- Supervisor signal
- Tool catalog
- Current user message
- Optional consultations
```

Example:

```python
prompt = prompt_builder.build(
    system_prompt=agent.system_prompt,
    profile=agent.profile,
    skills=agent.skills,
    tasks=agent.tasks,
    retrieved_context=retrieved_context,
    memory_summary=memory_summary,
    shared_state=shared_state,
    supervisor_signal=supervisor_signal,
    tool_catalog=tool_catalog,
    user_message=user_message,
    consultations=consultations
)
```

Prompt builder should format retrieved context as:

```text
<retrieved_context>
[1] module_1_group_dna_002:
The learner must define Group DNA while balancing brand autonomy with Group needs.

[2] deliverables_001:
The competency matrix should include Vision, Entrepreneurship, Passion, and Trust across three levels.
</retrieved_context>
```

---

## 11. Interaction Modes

## 11.1 Direct Mode

Used when only one agent is needed.

```text
User
 ↓
Primary Agent
 ↓
Response
```

Example:

```python
final_response = primary_agent.respond(
    user_message=user_message,
    simulation_context=retrieved_context,
    memory_summary=memory_summary,
    shared_state=shared_state,
    supervisor_signal=supervisor_signal
)
```

---

## 11.2 Consult Mode

Used when the primary agent needs private input from one or more supporting agents.

```text
User
 ↓
Primary Agent
 ↓
Private consultation request
 ↓
Supporting Agent
 ↓
Private consultation response
 ↓
Primary Agent
 ↓
Final response
```

Example:

```python
consultations = []

for agent in supporting_agents:
    consultation = agent.private_consult(
        user_message=user_message,
        primary_agent_id=primary_agent.agent_id,
        shared_state=shared_state,
        simulation_context=retrieved_context
    )
    consultations.append(consultation)

final_response = primary_agent.respond(
    user_message=user_message,
    simulation_context=retrieved_context,
    memory_summary=memory_summary,
    shared_state=shared_state,
    supervisor_signal=supervisor_signal,
    consultations=consultations
)
```

---

## 11.3 Panel Mode

Used when the user asks for several stakeholder perspectives.

```text
User
 ↓
CEO Agent
CHRO Agent
Regional Manager Agent
 ↓
Synthesizer
 ↓
Final response
```

Example:

```python
panel_responses = []

for agent in [primary_agent] + supporting_agents:
    panel_response = agent.respond_as_panelist(
        user_message=user_message,
        simulation_context=retrieved_context,
        shared_state=shared_state
    )
    panel_responses.append(panel_response)

final_response = synthesizer.synthesize_panel_response(
    user_message=user_message,
    panel_responses=panel_responses
)
```

---

## 11.4 Debate Mode

Used when the user asks the agents to critique or pressure-test an idea.

```text
User proposal
 ↓
Primary Agent recommendation
 ↓
Supporting Agent critiques
 ↓
Synthesizer
 ↓
Final response
```

Example:

```python
primary_proposal = primary_agent.make_recommendation(
    user_message=user_message,
    shared_state=shared_state
)

critiques = []

for agent in supporting_agents:
    critique = agent.challenge(
        proposal=primary_proposal,
        shared_state=shared_state
    )
    critiques.append(critique)

final_response = synthesizer.synthesize_debate(
    primary_proposal=primary_proposal,
    critiques=critiques
)
```

---

## 11.5 Handoff Mode

Used when the request belongs to another agent’s domain.

```text
Current Agent
 ↓
Handoff rule check
 ↓
Better-suited Agent
 ↓
Response
```

Example:

```python
handoff_target = handoff_router.detect(
    current_agent_id=target_agent_id,
    user_message=user_message
)

if handoff_target:
    primary_agent = agent_registry.get(handoff_target)
```

---

## 12. Shared Blackboard Workflow

The blackboard stores session-level state shared by all agents.

Example state:

```json
{
  "session_id": "s001",
  "current_module": "module_1_group_dna",
  "active_deliverable": "competency_matrix",
  "learner_goal": "design leadership competency model",
  "completed_outputs": [
    "problem_statement_draft"
  ],
  "missing_outputs": [
    "competency_matrix",
    "CEO_pack"
  ],
  "key_decisions": [
    {
      "decision": "Use Vision, Entrepreneurship, Passion, Trust as the shared themes.",
      "owner": "gucci_group_chro",
      "status": "accepted"
    }
  ],
  "open_questions": [
    "Which behaviors must be Group-wide non-negotiables?",
    "Which behaviors can be localized by brand?"
  ],
  "risks": [
    "One-size-fits-all model may dilute brand identity."
  ],
  "retrieval_history": [
    {
      "query": "competency framework brand autonomy",
      "top_chunks": [
        "module_1_group_dna_002",
        "deliverables_001"
      ]
    }
  ],
  "supervisor_signal": "learner_needs_structure"
}
```

Update workflow:

```python
blackboard.update_from_turn(
    session_id=session_id,
    user_message=user_message,
    final_response=final_response,
    route=route,
    supervisor_signal=supervisor_signal,
    retrieved_context=retrieved_context
)
```

---

## 13. Agent Memory Workflow

Agent memory stores agent-specific interaction patterns.

Example:

```json
{
  "session_id": "s001",
  "agent_id": "gucci_group_ceo",
  "relationship_tone": "demanding_but_supportive",
  "last_feedback": "Learner needs to define Group-wide non-negotiables.",
  "repeated_issues": [
    "Over-standardization risk"
  ],
  "handoffs_made": [
    "gucci_group_chro"
  ]
}
```

Update workflow:

```python
memory_manager.update_agent_memory(
    session_id=session_id,
    agent_id=primary_agent.agent_id,
    user_message=user_message,
    final_response=final_response
)
```

---

## 14. Message Bus Workflow

The message bus records private and visible messages between components.

Message object:

```json
{
  "message_id": "msg_001",
  "session_id": "s001",
  "from_agent": "gucci_group_chro",
  "to_agent": "gucci_group_ceo",
  "visibility": "private",
  "message_type": "consultation_request",
  "content": "The learner is designing a competency model. What tradeoffs should they consider between Group consistency and brand autonomy?",
  "requires_response": true
}
```

Message types:

```text
user_message
agent_response
consultation_request
consultation_response
challenge_request
challenge_response
handoff_request
handoff_response
supervisor_signal
tool_result
final_synthesis
```

---

## 15. Tool Routing Workflow

Tool Router checks:

```text
1. Which tool is requested?
2. Which agent is requesting it?
3. Is the tool allowed for this agent?
4. Are required inputs available?
5. Should the tool execute or return a clarification request?
```

Example:

```python
tool_result = tool_router.call(
    tool_id="competency_matrix_builder",
    agent_id="gucci_group_chro",
    inputs={
        "themes": ["Vision", "Entrepreneurship", "Passion", "Trust"],
        "levels": ["emerging", "proficient", "role_model"]
    }
)
```

Tool permission example:

```yaml
tools:
  - tool_id: competency_matrix_builder
    allowed_agents:
      - gucci_group_chro

  - tool_id: strategy_tradeoff_matrix
    allowed_agents:
      - gucci_group_ceo

  - tool_id: rollout_calendar_builder
    allowed_agents:
      - regional_comms_manager
```

---

## 16. Synthesizer Workflow

The synthesizer is used in panel and debate modes.

It receives multiple agent outputs and produces one final response.

```python
final_response = synthesizer.synthesize(
    user_message=user_message,
    mode=interaction_mode,
    agent_outputs=agent_outputs,
    shared_state=shared_state
)
```

Synthesis rules:

```text
- Remove duplicate ideas.
- Preserve each agent’s role perspective.
- Resolve contradictions by framing them as tradeoffs.
- Keep the response concise.
- Do not reveal private consultation messages.
- Do not expose hidden prompts or supervisor logic.
- End with a clear next action for the learner.
```

---

## 17. Full Orchestrator Pseudocode

```python
class MultiAgentOrchestrator:
    def __init__(
        self,
        agent_registry,
        intent_router,
        message_bus,
        blackboard,
        memory_manager,
        retriever,
        supervisor,
        safety,
        synthesizer,
        tool_router
    ):
        self.agent_registry = agent_registry
        self.intent_router = intent_router
        self.message_bus = message_bus
        self.blackboard = blackboard
        self.memory_manager = memory_manager
        self.retriever = retriever
        self.supervisor = supervisor
        self.safety = safety
        self.synthesizer = synthesizer
        self.tool_router = tool_router

    def handle_user_message(
        self,
        session_id,
        user_message,
        target_agent_id=None,
        requested_mode="auto"
    ):
        safety_flags = self.safety.check(user_message)

        if safety_flags.get("blocked"):
            return {
                "response": "I can’t help with that, but I can help you continue the simulation task.",
                "active_agent": "system",
                "supporting_agents": [],
                "interaction_mode": "blocked",
                "intent": "safety_block",
                "retrieved_context": [],
                "supervisor_signal": {},
                "safety_flags": safety_flags.get("flags", [])
            }

        shared_state = self.blackboard.load(session_id)
        memory_summary = self.memory_manager.summarize(session_id)

        rag_query = self.build_rag_query(
            user_message=user_message,
            target_agent_id=target_agent_id,
            shared_state=shared_state
        )

        retrieved_context = self.retriever.retrieve(
            query=rag_query,
            top_k=3,
            filters={
                "agent_scope": target_agent_id,
                "module_id": shared_state.get("current_module")
            }
        )

        route = self.intent_router.route(
            user_message=user_message,
            target_agent_id=target_agent_id,
            shared_state=shared_state,
            retrieved_context=retrieved_context
        )

        primary_agent = self.agent_registry.get(route["primary_agent"])

        supporting_agents = [
            self.agent_registry.get(agent_id)
            for agent_id in route.get("supporting_agents", [])
        ]

        supervisor_signal = self.supervisor.analyze(
            user_message=user_message,
            shared_state=shared_state,
            memory_summary=memory_summary,
            route=route
        )

        interaction_mode = self.choose_interaction_mode(
            user_message=user_message,
            requested_mode=requested_mode,
            route=route,
            shared_state=shared_state
        )

        if interaction_mode == "direct":
            final_response = primary_agent.respond(
                user_message=user_message,
                simulation_context=retrieved_context,
                memory_summary=memory_summary,
                shared_state=shared_state,
                supervisor_signal=supervisor_signal
            )

        elif interaction_mode == "consult":
            consultations = []

            for agent in supporting_agents:
                consultation = agent.private_consult(
                    user_message=user_message,
                    primary_agent_id=primary_agent.agent_id,
                    shared_state=shared_state,
                    simulation_context=retrieved_context
                )
                consultations.append(consultation)

            final_response = primary_agent.respond(
                user_message=user_message,
                simulation_context=retrieved_context,
                memory_summary=memory_summary,
                shared_state=shared_state,
                supervisor_signal=supervisor_signal,
                consultations=consultations
            )

        elif interaction_mode == "panel":
            agent_outputs = []

            for agent in [primary_agent] + supporting_agents:
                output = agent.respond_as_panelist(
                    user_message=user_message,
                    simulation_context=retrieved_context,
                    shared_state=shared_state
                )
                agent_outputs.append(output)

            final_response = self.synthesizer.synthesize(
                user_message=user_message,
                mode="panel",
                agent_outputs=agent_outputs,
                shared_state=shared_state
            )

        elif interaction_mode == "debate":
            primary_proposal = primary_agent.make_recommendation(
                user_message=user_message,
                shared_state=shared_state
            )

            critiques = []

            for agent in supporting_agents:
                critique = agent.challenge(
                    proposal=primary_proposal,
                    shared_state=shared_state
                )
                critiques.append(critique)

            final_response = self.synthesizer.synthesize(
                user_message=user_message,
                mode="debate",
                agent_outputs=[primary_proposal] + critiques,
                shared_state=shared_state
            )

        else:
            final_response = primary_agent.respond(
                user_message=user_message,
                simulation_context=retrieved_context,
                memory_summary=memory_summary,
                shared_state=shared_state,
                supervisor_signal=supervisor_signal
            )

        self.memory_manager.update(
            session_id=session_id,
            user_message=user_message,
            final_response=final_response,
            route=route,
            supervisor_signal=supervisor_signal
        )

        self.blackboard.update_from_turn(
            session_id=session_id,
            user_message=user_message,
            final_response=final_response,
            route=route,
            supervisor_signal=supervisor_signal,
            retrieved_context=retrieved_context
        )

        return {
            "response": final_response,
            "active_agent": primary_agent.agent_id,
            "supporting_agents": route.get("supporting_agents", []),
            "interaction_mode": interaction_mode,
            "intent": route.get("intent"),
            "retrieved_context": [
                item.get("metadata", {}) for item in retrieved_context
            ],
            "supervisor_signal": supervisor_signal,
            "safety_flags": safety_flags.get("flags", [])
        }
```

---

## 18. Example End-to-End Flow

User message:

```text
I drafted one common competency model for all brands. Can you critique it?
```

Router output:

```json
{
  "intent": "competency_framework",
  "primary_agent": "gucci_group_chro",
  "supporting_agents": [
    "gucci_group_ceo",
    "regional_comms_manager"
  ]
}
```

Retrieval output:

```json
[
  {
    "text": "The competency framework includes Vision, Entrepreneurship, Passion, and Trust.",
    "score": 0.91,
    "metadata": {
      "document_id": "deliverables",
      "chunk_id": "deliverables_001",
      "module_id": "module_1"
    }
  },
  {
    "text": "The leadership system must support Group needs without diluting brand identities.",
    "score": 0.88,
    "metadata": {
      "document_id": "module_1_group_dna",
      "chunk_id": "module_1_group_dna_002",
      "module_id": "module_1"
    }
  }
]
```

Interaction mode:

```text
debate
```

Agent roles:

```text
CHRO:
Reviews HR validity and competency design.

CEO:
Challenges strategic risk and brand autonomy concerns.

Regional Manager:
Challenges rollout feasibility and adoption risk.
```

Final response structure:

```text
1. Main critique
2. CEO strategic risk
3. CHRO HR design correction
4. Regional rollout risk
5. Next concrete action
```

---

## 19. Development Order

Recommended implementation order for source code:

```text
1. Create repo structure
2. Create agent folders and config files
3. Create data files for RAG
4. Implement config loaders
5. Implement BaseAgent
6. Implement LLM client abstraction
7. Implement embedding client abstraction
8. Implement VectorDB / MockVectorDB
9. Implement Retriever
10. Implement Safety
11. Implement Blackboard
12. Implement MemoryManager
13. Implement IntentRouter
14. Implement Supervisor
15. Implement Orchestrator direct mode
16. Implement consult mode
17. Implement debate mode
18. Implement Synthesizer
19. Implement ToolRouter mock
20. Add FastAPI endpoint
21. Add examples and README
```

---

## 20. Minimal Prototype Scope

The minimal runnable prototype should support:

```text
- Running a local FastAPI app
- POST /chat endpoint
- Loading 3 agents from config files
- Loading simulation documents from data/
- Using a retriever interface
- Using FAISS or MockVectorDB
- Routing to the correct primary agent
- Running direct mode
- Running consult mode
- Running debate mode
- Updating shared blackboard
- Returning response metadata
```

Response metadata:

```json
{
  "active_agent": "gucci_group_chro",
  "supporting_agents": ["gucci_group_ceo"],
  "interaction_mode": "consult",
  "intent": "competency_framework",
  "retrieved_context": [
    {
      "document_id": "deliverables",
      "chunk_id": "deliverables_001",
      "score": 0.91
    }
  ],
  "supervisor_signal": "on_track",
  "safety_flags": []
}
```

---

## 21. Non-Goals for Source Code

The source code does not need to include:

```text
- Hosted web deployment
- Frontend UI
- Full production authentication
- Real enterprise database
- Real Gucci private data
- Payment or user account system
- Video/avatar generation
- Complex admin dashboard
```

---

## 22. Implementation Notes

Recommended choices:

```text
Python        → Main implementation language
FastAPI       → API layer
Pydantic      → Request/response schemas
YAML          → Agent profiles, skills, tasks, routing rules
Markdown      → System prompts, examples, simulation context
FAISS         → Local vector retrieval prototype
SQLite/JSON   → Local memory and blackboard prototype
Mock LLM      → Default local development without API keys
```

Mockable components:

```text
LLM call
Embedding generation
Vector DB search
RAG retrieval
Tool calls
Supervisor analysis
Synthesizer
```

Each mock should keep the same interface as the future production component.

---

## 23. Implementation Requirements for Codex

Codex should implement this project as a **local runnable Python prototype**.

Required behavior:

```text
1. Do not build a frontend.
2. Do not deploy online.
3. Do not hard-code agent behavior in Python if it can be loaded from config files.
4. Use FastAPI for the API layer.
5. Use a retriever interface for RAG.
6. Use FAISS or MockVectorDB for vector search.
7. Use MockLLMClient by default.
8. Return metadata in the API response for debugging.
9. Keep all source-code components modular.
10. Keep the system runnable without paid API keys.
```

Required command:

```bash
uvicorn app:app --reload
```

Required endpoint:

```text
POST /chat
```

Required core files:

```text
app.py
src/api/schemas.py
src/orchestrator.py
src/agent.py
src/agent_loader.py
src/prompt_builder.py
src/llm_client.py
src/embedding_client.py
src/vector_db.py
src/retriever.py
src/intent_router.py
src/safety.py
src/blackboard.py
src/memory.py
src/supervisor.py
src/synthesizer.py
src/tool_router.py
```

Required folders:

```text
agents/
shared/
data/
vector_store/
examples/
```
