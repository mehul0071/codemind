from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import codebase
from app.api import query

app = FastAPI(
    title="CodeMind",
    description="Agentic Codebase Intelligence Platform",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(codebase.router, prefix="/api/v1", tags=["codebase"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])

@app.get("/")
async def root():
    return {"message": "CodeMind API is working and live"}