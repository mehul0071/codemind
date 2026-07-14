from fastapi import APIRouter
from app.schemas.query import QueryRequest, QueryResponse
from app.services.retrieval_service import RetrievalService

router = APIRouter()

@router.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest):
    service = RetrievalService()
    result = await service.get_answer(request.query, request.session_id)
    return result