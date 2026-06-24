# Multi-Agent AI Co-worker Engine

Local FastAPI prototype for a Gucci HRM AI co-worker simulation. The app exposes a browser chat UI and API endpoints for a small multi-agent system with configurable agent profiles, RAG-style retrieval, blackboard memory, safety checks, and mock/Gemini LLM clients.

For step-by-step setup, see [RUNNING.md](RUNNING.md).

## What Is Included

- Browser chat UI at `/`
- FastAPI endpoints for health, agents, and chat
- Four selectable agents:
  - `gucci_group_boss`
  - `gucci_group_ceo`
  - `gucci_group_chro`
  - `regional_comms_manager`
- Boss agent that coordinates the specialist agents
- Mock LLM mode for local review without paid keys
- Optional Gemini mode through `.env`
- Tests for routing, safety, API behavior, and mock output

## Quick Start

```powershell
cd ai-coworker-engine
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
```

Open:

```text
http://127.0.0.1:8001
```

Run tests:

```powershell
python -m pytest -q
```

## Project Structure

```text
ai-coworker-engine/
|-- app.py                  # FastAPI app entrypoint
|-- README.md               # Project overview
|-- RUNNING.md              # Local setup and run guide
|-- requirements.txt
|-- .env.example
|
|-- agents/                 # Agent configs and prompts
|   |-- gucci_group_boss/
|   |-- gucci_group_ceo/
|   |-- gucci_group_chro/
|   `-- regional_comms_manager/
|
|-- data/                   # RAG knowledge files
|-- examples/               # Example conversations
|-- shared/                 # Shared prompt, rules, and tools
|
|-- src/
|   |-- api/                # FastAPI route/schema modules
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
|
|-- static/                 # Browser UI
|-- tests/
`-- workflow.md             # Original assignment/workflow reference
```

## API Summary

Health:

```http
GET /health
```

Agents:

```http
GET /api/agents
```

Chat with selected agent:

```http
POST /chat/{agent_id}
Content-Type: application/json

{
  "session_id": "demo-session",
  "message": "I need to build an education communication project."
}
```

Advanced chat:

```http
POST /chat
Content-Type: application/json

{
  "session_id": "demo-session",
  "target_agent_id": "gucci_group_boss",
  "mode": "auto",
  "message": "Ask the team to pressure-test my plan."
}
```

Supported modes:

- `auto`
- `direct`
- `consult`
- `panel`
- `debate`
- `handoff`

## Notes

- The app defaults to mock mode, so it works offline and does not require paid API keys.
- Hidden system prompts are not exposed through the UI or API preview route.
- Runtime files such as `.env`, logs, caches, and generated vector-store files are ignored by git.
