from pydantic import BaseModel
from typing import Optional, List


class ReviewRequest(BaseModel):
    session_id: str 
    file_path: Optional[str] = None
    focus: Optional[str] = None


class ReviewIssue(BaseModel):
    file_path: str
    line: Optional[int] = None
    severity: str  # e.g., info, warning, critical
    message: str
    suggestion: Optional[str] = None


class ReviewResponse(BaseModel):
    session_id: str
    summary: str
    score: Optional[float] = None  # e.g., code quality/security score 0-100
    issues: List[ReviewIssue]
    success: bool