from fastapi import APIRouter, Request
from app.schemas.query import QueryRequest, QueryResponse
from app.services.retrieval_service import RetrievalService
from app.utils.rate_limit import limiter

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query_codebase(request: Request, payload: QueryRequest):
    service = RetrievalService()
    result = await service.get_answer(payload.query, payload.session_id)
    return result