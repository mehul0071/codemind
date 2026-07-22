from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    query: str
    session_id: str
    task_type: Optional[str]
    files_retrieved: List[str]
    retrieved_context: List[str]
    analysis: Optional[str]
    generated_patch: Optional[str]
    lint_results: Optional[Dict[str, Any]]
    test_results: Optional[Dict[str, Any]]
    review_feedback: Optional[str]
    iteration_count: int
    is_complete: bool
