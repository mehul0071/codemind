import os
from git import Repo
from app.config import settings
from datetime import datetime
from sqlalchemy import select
from app.db.models.repository import Repository
from app.parsers.python_parser import PythonParser
from app.rag.chunker import CodeChunker
from app.schemas.repository import IngestRequest, IngestResponse
from app.vectorstore.chroma import ChromaVectorStore
from app.db.sessions import AsyncSessionLocal


class IngestionService:

    def __init__(self):
        self.parser = PythonParser()
        self.chunker = CodeChunker()
        self.vector_store = ChromaVectorStore()

    async def ingestion(self, request: IngestRequest) -> IngestResponse:
        session_id = request.session_id
        repo_name = "unknown"

        try:
            await self._update_repo_status(session_id, "pending", repo_name)

            target_path = await self._prepare_repo(request)
            repo_name = os.path.basename(target_path)
            parsed_elements = self.parser.parse_file(target_path)
            documents = self.chunker.create_chunks(parsed_elements)
            chunk_count = self.vector_store.add_documents(documents, session_id)

            await self.__update_repo_status(session_id, "completed", repo_name,
                files_processed=len(parsed_elements),
                chunks_created=chunk_count
            )

            return IngestResponse(
                status="success",
                message="code is successfully ingested in codemind",
                session_id=session_id,
                files_processed=len(parsed_elements),
                chunks_created=chunk_count,
                repo_name=repo_name,
                ingested_at=datetime.utcnow() 
            )

        except Exception as e:
            print(f"code ingstion has failed in codemind , {e}")
            await self._update_repo_status(session_id, "failed", repo_name)
            raise


    async def _prepare_repo(self, request: IngestRequest) -> str:
        if request.local_path and os.path.exists(request.local_path):
            return request.local_path
        
        if request.repo_url:
            target_dir = os.path.join(settings.DATA_PATH, request.session_id)
            os.makedirs(target_dir, exist_ok=True)
            repo_name = request.repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            clone_path = os.path.join(target_dir, repo_name)

            if os.path.exists(clone_path):
                print(f"repo you are trying to clone is already cloned, repo already exists at {clone_path}")
                return
        
            print(f"Cloning the requested repo{request.repo_url} ...")
            Repo.clone_from(request.repo_url, clone_path)
            return clone_path
        
        raise ValueError("Please provide either repo_url or local_path")
    

    async def _update_repo_status(self, session_id: str, status: str, 
                                repo_name: str, files_processed: int = 0, 
                                chunks_created: int = 0):
        async with AsyncSessionLocal() as db:
            stmt = select(Repository).where(Repository.session_id == session_id)
            result = db.execute(stmt)
            repo = result.scalar_one_or_none()

            if not repo:
                repo = Repository(
                    session_id=session_id,
                    repo_url="",
                    status=status,
                    metadata_info={
                        "repo_name": repo_name,
                        "files_processed": files_processed,
                        "chunks_created": chunks_created
                    }
                )
                db.add(repo)
            else:
                repo.status = status
                repo.metadata_info = {
                    "repo_name": repo_name,
                    "files_processed": files_processed,
                    "chunks_created": chunks_created
                }
            await db.commit()