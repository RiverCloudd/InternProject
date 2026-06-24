# Running the Project

This guide is written for a reviewer running the project on a fresh machine.
The app runs locally and does not require a paid API key by default.

## Requirements

- Python 3.10 or newer
- `pip`
- A terminal or command prompt

## 1. Open the Project Folder

From the folder where you downloaded or cloned the project:

```bash
cd ai-coworker-engine
```

If the project folder has a different name, `cd` into that folder instead.

## 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If PowerShell blocks activation on Windows, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 3. Install Dependencies

Windows:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 4. Run the App

Windows:

```powershell
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
```

macOS/Linux:

```bash
python3 -m uvicorn app:app --reload --host 127.0.0.1 --port 8001
```

Then open:

```text
http://127.0.0.1:8001
```

## 5. Run Tests

Windows:

```powershell
python -m pytest -q
```

macOS/Linux:

```bash
python3 -m pytest -q
```

## Default LLM Mode

The project uses `MockLLMClient` by default. This means the app can be reviewed locally without any external API key.

The mock client is deterministic and returns structured English responses for demo and grading purposes.

## Optional Gemini Setup

Gemini is optional. To enable it, copy the example environment file:

Windows:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env`:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=YOUR_REAL_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash
```

Then restart the app.

Do not commit `.env`. It is intentionally ignored by git.

## Main Pages and Endpoints

Browser UI:

```text
http://127.0.0.1:8001
```

Health check:

```text
GET /health
```

Agent list:

```text
GET /api/agents
```

Chat with an agent:

```text
POST /chat/{agent_id}
```

Available agent IDs:

- `gucci_group_boss`
- `gucci_group_ceo`
- `gucci_group_chro`
- `regional_comms_manager`

Example request body:

```json
{
  "session_id": "demo-session",
  "message": "I need to build an education communication project."
}
```

## Troubleshooting

If port `8001` is already in use, run the app on another port:

```bash
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8002
```

Then open:

```text
http://127.0.0.1:8002
```

If the browser shows an old version of the UI, hard refresh the page:

- Windows/Linux: `Ctrl + F5`
- macOS: `Cmd + Shift + R`

If dependencies are missing, make sure the virtual environment is activated and reinstall:

```bash
python -m pip install -r requirements.txt
```
