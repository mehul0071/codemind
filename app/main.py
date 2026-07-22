import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import codebase, query
from app.api import agent, health
from app.middleware.auth import APIKeyMiddleware

# ── Logging setup ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("codemind")

# ── FastAPI app ────────────────────────────────────────────────────────────
app = FastAPI(
    title="CodeMind",
    description=(
        "Agentic Codebase Intelligence Platform.\n\n"
        "Ingest any Python repository, ask questions, and get AI-generated "
        "code patches with self-correcting LangGraph multi-agent orchestration."
    ),
    version="0.2.0",
)

# ── Middleware ─────────────────────────────────────────────────────────────
app.add_middleware(APIKeyMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        f'{{"method":"{request.method}","path":"{request.url.path}",'
        f'"status":{response.status_code},"duration_ms":{duration_ms}}}'
    )
    return response


# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(codebase.router, prefix="/api/v1", tags=["codebase"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])


@app.get("/")
async def root():
    return {"message": "CodeMind API is running", "docs": "/docs", "health": "/health"}