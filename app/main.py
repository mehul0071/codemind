from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import codebase, query, review


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


app.include_router(codebase.router, prefix="/api/v1", tags=["Codebase"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(review.router, prefix="/api/v1", tags=["Review"])


@app.get("/")
async def root():
    return {"message": "CodeMind API is Working"}