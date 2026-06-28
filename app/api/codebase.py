from fastapi import APIRouter, HTTPException
from app.schemas.repository import IngestRequest
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.post("/ingest_code")
async def ingest_codebase(request=IngestRequest):
    try:
        service = IngestionService()
        result = service.ingest(request)
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/status/{session_id}")
async def get_ingestion_status(session_id: str):

    return {"session_id": session_id, "status": "not_implemented_yet"}