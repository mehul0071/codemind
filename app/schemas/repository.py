from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class IngestRequest(BaseModel):
    repo_url: Optional[str] = None
    local_path: Optional[str] = None
    session_id: str

    class Config:
        extra = "forbid"


class IngestResponse(BaseModel):
    status: str
    message: str
    session_id: str
    files_processed: int
    chunks_created: int
    repo_name: Optional[str] = None
    ingested_at: datetime

    class Config:
        arbitrary_types_allowed = True