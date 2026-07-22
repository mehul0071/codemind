from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.repository import IngestRequest, IngestAcceptedResponse, IngestStatusResponse
from app.services.ingestion_service import IngestionService
from app.db.sessions import get_db
from app.db.models.repository import Repository
from app.db.models.user import User
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/ingest_code", status_code=202, response_model=IngestAcceptedResponse)
async def ingest_codebase(request: IngestRequest, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    try:
        service = IngestionService()
        background_tasks.add_task(service.ingestion, request, str(current_user.id))
        return {
            "status": "accepted",
            "message": "code ingestion is successfully started in the background",
            "session_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ingestion: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=IngestStatusResponse)
async def get_ingestion_status(session_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        stmt = select(Repository).where(
            Repository.session_id == session_id,
            Repository.user_id == current_user.id
        )
        result = await db.execute(stmt)
        repo = result.scalar_one_or_none()

        if not repo:
            raise HTTPException(
                status_code=404,
                detail=f"Ingestion session '{session_id}' not found"
            )

        return {
            "session_id": session_id,
            "status": repo.status.value if hasattr(repo.status, "value") else repo.status,
            "repo_url": repo.repo_url,
            "local_path": repo.local_path,
            "metadata": repo.metadata_info,
            "created_at": repo.created_at,
            "updated_at": repo.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve status: {str(e)}"
        )