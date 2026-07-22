from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional, List
from app.services.planning_service import PlanningService
from app.schemas.agent import AgentGenerateRequest, AgentGenerateResponse
from app.utils.rate_limit import limiter

router = APIRouter()

@router.post("/generate", response_model=AgentGenerateResponse)
@limiter.limit("10/minute")
async def generate_code(request: Request, payload: AgentGenerateRequest):

    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if not payload.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id cannot be empty.")

    try:
        service = PlanningService()
        result = await service.run(
            query=payload.query,
            session_id=payload.session_id,
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
