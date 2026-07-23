from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import BASE_DIR, settings
from app.schemas import HealthResponse, QuestionRequest, QuestionResponse, SourceItem
from app.services.agent import CampusAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = CampusAgent(settings)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Agente RAG para consultar documentos CSV o PDF.",
    version="1.0.0",
    lifespan=lifespan,
)

STATIC_DIR = BASE_DIR / "app" / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    agent: CampusAgent = request.app.state.agent
    return HealthResponse(
        status="ok",
        document=Path(settings.data_path).name,
        chunks=len(agent.chunks),
        llm_enabled=bool(settings.gemini_api_key),
    )


@app.get("/api/document-summary")
def document_summary(request: Request) -> dict:
    agent: CampusAgent = request.app.state.agent
    categories = sorted(
        {
            chunk.metadata.get("category")
            for chunk in agent.chunks
            if chunk.metadata.get("category")
        }
    )
    return {
        "document": Path(settings.data_path).name,
        "records": len(agent.chunks),
        "categories": categories,
    }


@app.post("/api/ask", response_model=QuestionResponse)
def ask(payload: QuestionRequest, request: Request) -> QuestionResponse:
    agent: CampusAgent = request.app.state.agent
    try:
        result = agent.answer(payload.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo procesar la pregunta: {exc}") from exc

    sources = []
    for item in result.results:
        metadata = item.chunk.metadata
        sources.append(
            SourceItem(
                title=item.chunk.source,
                file=metadata.get("file", "documento"),
                category=metadata.get("category") or None,
                page=metadata.get("page"),
                row=metadata.get("row"),
                contact=metadata.get("contact") or None,
                url=metadata.get("url") or None,
                relevance=round(item.score, 4),
                excerpt=item.chunk.text[:420],
            )
        )

    return QuestionResponse(answer=result.answer, mode=result.mode, sources=sources)


@app.post("/api/reload")
def reload_document(request: Request) -> dict:
    agent: CampusAgent = request.app.state.agent
    count = agent.reload()
    return {"status": "reloaded", "chunks": count}
