from fastapi import APIRouter, HTTPException
from app.schemas.repository import IngestRequest
from app.services.ingestion_service import IngestionService

router = APIRouter()

@router.post("/ingest_code")
async def ingest_codebase(request: IngestRequest):
    try:
        service = IngestionService()
        result = await service.ingestion(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Ingestion failed: {str(e)}"
        )
    

@router.get("/status/{session_id}")
async def get_ingestion_status(session_id: str):

    return {"session_id": session_id, "status": "not_implemented_yet"}