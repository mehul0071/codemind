import os
from git import Repo
from app.config import settings
from datetime import datetime, timezone
from sqlalchemy import select, delete
from app.db.models.repository import Repository
from app.db.models.document_chunk import DocumentChunk
from app.parsers.python_parser import PythonParser
from app.rag.chunker import CodeChunker
from app.schemas.repository import IngestRequest, IngestResponse
from app.db.sessions import AsyncSessionLocal
from langchain_huggingface import HuggingFaceEmbeddings


class IngestionService:

    def __init__(self):
        self.parser = PythonParser()
        self.chunker = CodeChunker()
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )

    async def ingestion(self, request: IngestRequest) -> IngestResponse:
        session_id = request.session_id
        repo_name = "unknown"

        try:
            repo_id = await self._update_repo_status(session_id, "PENDING", repo_name)
            
            target_path = await self._prepare_repo(request)
            repo_name = os.path.basename(target_path)
            
            # Update status to processing
            repo_id = await self._update_repo_status(session_id, "PROCESSING", repo_name)
            
            parsed_elements = self.parser.parse_directory(target_path)
            documents = self.chunker.create_chunks(parsed_elements)
            
            if documents:
                texts = [doc.page_content for doc in documents]
                embeddings = self.embeddings.embed_documents(texts)
                
                async with AsyncSessionLocal() as db:
                    # Clean up existing chunks for this session to support re-ingestion
                    await db.execute(
                        delete(DocumentChunk).where(DocumentChunk.session_id == session_id)
                    )
                    
                    chunk_objs = []
                    for doc, emb in zip(documents, embeddings):
                        chunk_objs.append(DocumentChunk(
                            repository_id=repo_id,
                            session_id=session_id,
                            file_path=doc.metadata.get("file_path"),
                            name=doc.metadata.get("name"),
                            type=doc.metadata.get("type"),
                            content=doc.page_content,
                            embedding=emb
                        ))
                    db.add_all(chunk_objs)
                    await db.commit()
                chunk_count = len(documents)
            else:
                chunk_count = 0

            files_processed = len(
                {element["file_path"] for element in parsed_elements}
            )
            await self._update_repo_status(session_id, "COMPLETED", repo_name,
                files_processed=files_processed,
                chunks_created=chunk_count
            )

            return IngestResponse(
                status="success",
                message="code is successfully ingested in codemind",
                session_id=session_id,
                files_processed=files_processed,
                chunks_created=chunk_count,
                repo_name=repo_name,
                ingested_at=datetime.now(timezone.utc)
            )

        except Exception as e:
            print(f"code ingstion has failed in codemind , {e}")
            await self._update_repo_status(session_id, "FAILED", repo_name)
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
                return clone_path
        
            print(f"Cloning the requested repo{request.repo_url} ...")
            Repo.clone_from(request.repo_url, clone_path)
            return clone_path
        
        raise ValueError("Please provide either repo_url or local_path")
    

    async def _update_repo_status(self, session_id: str, status: str, 
                                repo_name: str, files_processed: int = 0, 
                                chunks_created: int = 0) -> int:
        async with AsyncSessionLocal() as db:
            stmt = select(Repository).where(Repository.session_id == session_id)
            result = await db.execute(stmt)
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
            await db.refresh(repo)
            return repo.id

