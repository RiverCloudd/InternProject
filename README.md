# Multi-Agent AI Co-worker Engine

Local Python prototype for the Gucci HRM AI co-worker simulation. The implementation follows `workflow.md`: API-first, config-loaded agents, RAG retrieval, vector DB abstraction, LLM client abstraction, multi-agent orchestration, blackboard memory, and debug metadata.

## Agents

- `gucci_group_ceo`
- `gucci_group_chro`
- `regional_comms_manager`

Each agent lives in `agents/<agent_id>/` and includes:

- `profile.yaml`
- `system_prompt.md`
- `skills.yaml`
- `tasks.yaml`
- `memory_schema.yaml`
- `handoff_rules.yaml`
- `examples.md`

## Gemini API Key

The app runs with `MockLLMClient` by default, so no paid API key is required.

To use Gemini:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set:

```text
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_REAL_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash
```

Do not commit `.env`. The code reads the key through `src/config.py` and calls Gemini only through `src/llm_client.py`.

## Run

```bash
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

Open:

```text
http://127.0.0.1:8001
```

## Required API

### Health

```http
GET /health
```

### Agents

```http
GET /agents
```

### Chat

```http
POST /chat
Content-Type: application/json

{
  "session_id": "s001",
  "target_agent_id": "gucci_group_chro",
  "mode": "auto",
  "message": "Can you review my competency framework?"
}
```

Modes:

- `auto`
- `direct`
- `consult`
- `panel`
- `debate`
- `handoff`

Response includes:

- `response`
- `active_agent`
- `supporting_agents`
- `interaction_mode`
- `intent`
- `retrieved_context`
- `supervisor_signal`
- `safety_flags`
- `llm_provider`
- `blackboard`
- `message_bus`

## Source Structure

```text
ai-coworker-engine/
|-- app.py
|-- workflow.md
|-- requirements.txt
|-- .env.example
|
|-- agents/
|-- shared/
|-- data/
|-- vector_store/
|
|-- src/
|   |-- api/
|   |   |-- schemas.py
|   |   `-- routes.py
|   |-- agent.py
|   |-- agent_loader.py
|   |-- blackboard.py
|   |-- config.py
|   |-- embedding_client.py
|   |-- intent_router.py
|   |-- llm_client.py
|   |-- memory.py
|   |-- message_bus.py
|   |-- orchestrator.py
|   |-- prompt_builder.py
|   |-- retriever.py
|   |-- safety.py
|   |-- supervisor.py
|   |-- synthesizer.py
|   |-- tool_router.py
|   `-- vector_db.py
```

## RAG

`src/retriever.py` uses:

- `src/embedding_client.py`
- `src/vector_db.py`
- local files from `data/`, `shared/`, and `agents/`

The prototype uses mock embeddings and a local vector DB interface. This keeps the same production-compatible shape without requiring FAISS setup.

## Tests

```bash
python -m pytest -q
```
