from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import create_router
from src.orchestrator import MultiAgentOrchestrator


BASE_DIR = Path(__file__).parent


app = FastAPI(title="Multi-Agent AI Co-worker Engine")
orchestrator = MultiAgentOrchestrator.create_default(BASE_DIR)
app.include_router(create_router(orchestrator))

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=False)
