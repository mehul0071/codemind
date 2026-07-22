from fastapi import APIRouter, Request, Depends, HTTPException
from app.schemas.query import QueryRequest, QueryResponse
from app.services.retrieval_service import RetrievalService
from app.utils.rate_limit import limiter
from app.db.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query_codebase(request: Request, payload: QueryRequest, current_user: User = Depends(get_current_user)):
    service = RetrievalService()
    result = await service.get_answer(payload.query, payload.session_id, user_id=str(current_user.id))
    return result