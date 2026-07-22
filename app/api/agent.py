from fastapi import APIRouter, HTTPException, BackgroundTasks, Request, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.services.planning_service import PlanningService
from app.schemas.agent import AgentGenerateRequest, AgentGenerateResponse
from app.utils.rate_limit import limiter
from app.db.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/generate", response_model=AgentGenerateResponse)
@limiter.limit("10/minute")
async def generate_code(request: Request, payload: AgentGenerateRequest, current_user: User = Depends(get_current_user)):

    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if not payload.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id cannot be empty.")

    try:
        service = PlanningService()
        result = await service.run(
            query=payload.query,
            session_id=payload.session_id,
            user_id=str(current_user.id)
        )
        return AgentGenerateResponse(
            task_type=result.get("task_type", "CODE_TASK"),
            generated_patch=result.get("generated_patch"),
            review_feedback=result.get("review_feedback"),
            iteration_count=result.get("iteration_count", 0),
            is_complete=result.get("is_complete", False),
            files_retrieved=result.get("files_retrieved", []),
            analysis=result.get("analysis"),
            success=result.get("is_complete", False),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent pipeline failed: {str(e)}"
        )
