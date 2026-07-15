import os
import asyncio
from git import Repo
from app.config import settings
from datetime import datetime, timezone
from sqlalchemy import select, delete
from app.db.models.repository import Repository
from app.db.models.document_chunk import DocumentChunk
from app.db.models.code_relation import CodeRelation
from app.parsers.python_parser import PythonParser
from app.parsers.dependency_parser import DependencyParser
from app.rag.chunker import CodeChunker
from app.schemas.repository import IngestRequest, IngestResponse
from app.db.sessions import AsyncSessionLocal
from app.rag.embeddings import embeddings


class IngestionService:

    def __init__(self):
        self.parser = PythonParser()
        self.chunker = CodeChunker()
        self.embeddings = embeddings


    async def ingestion(self, request: IngestRequest) -> IngestResponse:
        session_id = request.session_id
        repo_name = "unknown"

        try:
            repo_id = await self._update_repo_status(
                session_id, "PENDING", repo_name,
                repo_url=request.repo_url, local_path=request.local_path
            )
            
            target_path = await self._prepare_repo(request)
            repo_name = os.path.basename(target_path)
            
            repo_id = await self._update_repo_status(
                session_id, "PROCESSING", repo_name,
                repo_url=request.repo_url, local_path=request.local_path
            )
            
            parsed_elements = self.parser.parse_directory(target_path)
            documents = self.chunker.create_chunks(parsed_elements)
            
            dep_parser = DependencyParser(repo_path=target_path)
            dep_map = dep_parser.parse_directory()
            
            relation_objs = []
            for file_rel_path, file_data in dep_map.items():
                for imp in file_data.get("imports", []):
                    if imp.get("is_local") and imp.get("resolved_project_relative_path"):
                        relation_objs.append(CodeRelation(
                            repository_id=repo_id,
                            session_id=session_id,
                            source_type="file",
                            source_name=file_rel_path,
                            target_type="file",
                            target_name=imp["resolved_project_relative_path"],
                            relation_type="imports",
                            metadata_info={
                                "line": imp.get("line"),
                                "imported_name": imp.get("imported_name"),
                                "alias": imp.get("alias"),
                                "module": imp.get("module")
                            }
                        ))
                
                for cls in file_data.get("classes", []):
                    for resolved_base in cls.get("resolved_bases", []):
                        relation_objs.append(CodeRelation(
                            repository_id=repo_id,
                            session_id=session_id,
                            source_type="class",
                            source_name=cls["name"],
                            target_type="class",
                            target_name=resolved_base,
                            relation_type="inherits",
                            metadata_info={
                                "line": cls.get("line"),
                                "end_line": cls.get("end_line"),
                                "file_path": file_rel_path
                            }
                        ))
                
                for call in file_data.get("calls", []):
                    relation_objs.append(CodeRelation(
                        repository_id=repo_id,
                        session_id=session_id,
                        source_type="function",
                        source_name=call["caller"],
                        target_type="function",
                        target_name=call["callee"],
                        relation_type="calls",
                        metadata_info={
                            "line": call.get("line"),
                            "file_path": file_rel_path
                        }
                    ))

            async with AsyncSessionLocal() as db:
                await db.execute(
                    delete(DocumentChunk).where(DocumentChunk.session_id == session_id)
                )
                await db.execute(
                    delete(CodeRelation).where(CodeRelation.session_id == session_id)
                )
                
                if documents:
                    texts = [doc.page_content for doc in documents]
                    embeddings = self.embeddings.embed_documents(texts)
                    
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
                    chunk_count = len(documents)
                else:
                    chunk_count = 0

                if relation_objs:
                    db.add_all(relation_objs)
                
                await db.commit()

            files_processed = len(
                {element["file_path"] for element in parsed_elements}
            )
            await self._update_repo_status(
                session_id, "COMPLETED", repo_name,
                files_processed=files_processed,
                chunks_created=chunk_count,
                repo_url=request.repo_url,
                local_path=request.local_path
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
            import traceback
            traceback.print_exc()
            print(f"code ingestion has failed in codemind , {e}")
            await self._update_repo_status(
                session_id, "FAILED", repo_name,
                repo_url=request.repo_url,
                local_path=request.local_path,
                error_message=str(e)
            )
            raise


    async def _prepare_repo(self, request: IngestRequest) -> str:
        if request.local_path:
            abs_path = os.path.abspath(request.local_path)
            if os.path.exists(abs_path):
                return abs_path
            raise ValueError(f"local_path '{request.local_path}' does not exist (resolved to: {abs_path})")
        
        if request.repo_url:
            target_dir = os.path.join(settings.DATA_PATH, request.session_id)
            os.makedirs(target_dir, exist_ok=True)
            repo_name = request.repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            clone_path = os.path.join(target_dir, repo_name)

            if os.path.exists(clone_path):
                print(f"repo you are trying to clone is already cloned, repo already exists at {clone_path}")
                return clone_path
        
            print(f"Cloning the requested repo {request.repo_url} ...")
            await asyncio.to_thread(Repo.clone_from, request.repo_url, clone_path)
            return clone_path
        
        raise ValueError("Please provide either repo_url or local_path")
    

    async def _update_repo_status(self, session_id: str, status: str, 
                                 repo_name: str, files_processed: int = 0, 
                                 chunks_created: int = 0,
                                 repo_url: str | None = None,
                                 local_path: str | None = None,
                                 error_message: str | None = None) -> int:
        async with AsyncSessionLocal() as db:
            stmt = select(Repository).where(Repository.session_id == session_id)
            result = await db.execute(stmt)
            repo = result.scalar_one_or_none()

            meta = {
                "repo_name": repo_name,
                "files_processed": files_processed,
                "chunks_created": chunks_created
            }
            if error_message:
                meta["error_message"] = error_message

            if not repo:
                repo = Repository(
                    session_id=session_id,
                    repo_url=repo_url or "",
                    local_path=local_path,
                    status=status,
                    metadata_info=meta
                )
                db.add(repo)
            else:
                repo.status = status
                repo.metadata_info = meta
                if repo_url is not None:
                    repo.repo_url = repo_url
                if local_path is not None:
                    repo.local_path = local_path

            await db.commit()
            await db.refresh(repo)
            return repo.id

