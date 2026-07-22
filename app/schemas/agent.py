from pydantic import BaseModel
from typing import List, Optional


class AgentGenerateRequest(BaseModel):
    query: str
    session_id: str


class AgentGenerateResponse(BaseModel):
    task_type: str
    generated_patch: Optional[str] = None
    review_feedback: Optional[str] = None
    iteration_count: int
    is_complete: bool
    files_retrieved: List[str] = []
    analysis: Optional[str] = None
    success: bool