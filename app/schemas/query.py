from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    query: str
    session_id: str


class SourceDocument(BaseModel):
    file_path: str
    type: str
    name: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    success: bool
    num_sources: int
    citations: Optional[List[str]] = None