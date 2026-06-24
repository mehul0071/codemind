from pydantic import BaseModel
from typing import Optional


class IngestRequest(BaseModel):
    repo_url: Optional[str] = None
    local_path: Optional[str] = None
    session_id: str