from typing import Dict, Any
from app.agents.graph import app_graph
from app.agents.state import AgentState
from app.db.sessions import AsyncSessionLocal
from app.db.models.repository import Repository
from sqlalchemy import select


class PlanningService:
    
    async def run(self, query: str, session_id: str, user_id: str) -> Dict[str, Any]:
        async with AsyncSessionLocal() as db:
            stmt = select(Repository).where(
                Repository.session_id == session_id,
                Repository.user_id == user_id
            )
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                return {
                    "is_complete": False,
                    "task_type": "UNKNOWN",
                    "generated_patch": None,
                    "review_feedback": "Unauthorized or repository not found.",
                    "iteration_count": 0,
                    "files_retrieved": [],
                    "analysis": "Unauthorized."
                }

        initial_state: AgentState = {
            "query": query,
            "session_id": session_id,
            "task_type": None,
            "files_retrieved": [],
            "retrieved_context": [],
            "analysis": None,
            "generated_patch": None,
            "lint_results": None,
            "test_results": None,
            "review_feedback": None,
            "iteration_count": 0,
            "is_complete": False,
        }

        final_state = await app_graph.ainvoke(initial_state)

        return {
            "generated_patch": final_state.get("generated_patch", ""),
            "review_feedback": final_state.get("review_feedback", ""),
            "iteration_count": final_state.get("iteration_count", 0),
            "is_complete": final_state.get("is_complete", False),
            "task_type": final_state.get("task_type", "CODE_TASK"),
            "files_retrieved": final_state.get("files_retrieved", []),
            "analysis": final_state.get("analysis", ""),
        }
