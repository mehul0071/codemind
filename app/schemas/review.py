from pydantic import BaseModel
from typing import Optional


class ReviewRequest(BaseModel):
    session_id: str 
    file_path: Optional[str] = None
    focus: Optional[str] = None