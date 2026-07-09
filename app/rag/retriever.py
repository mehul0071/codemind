from typing import List, Tuple
from langchain_core.documents import Document
from app.rag.embeddings import embeddings
from app.config import settings
from app.db.sessions import AsyncSessionLocal
from app.db.models.document_chunk import DocumentChunk
from sqlalchemy import select


class CodeRetriever:
    def __init__(self):
        self.embeddings = embeddings

    async def retrieve(self, query: str, session_id: str, k: int = 8) -> List[Document]:
        try:
            query_embedding = self.embeddings.embed_query(query)
            async with AsyncSessionLocal() as db:
                stmt = (
                    select(DocumentChunk)
                    .where(DocumentChunk.session_id == session_id)
                    .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
                    .limit(k)
                )
                result = await db.execute(stmt)
                chunks = result.scalars().all()
                
            docs = []
            for chunk in chunks:
                docs.append(Document(
                    page_content=chunk.content,
                    metadata={
                        "name": chunk.name,
                        "type": chunk.type,
                        "file_path": chunk.file_path,
                        "session_id": chunk.session_id
                    }
                ))
            return docs
        except Exception as e:
            print(f"Error in retrieve: {e}")
            return []

    async def retrieve_with_scores(self, query: str, session_id: str, k: int = 8) -> List[Tuple[Document, float]]:
        try:
            query_embedding = self.embeddings.embed_query(query)
            distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding)
            async with AsyncSessionLocal() as db:
                stmt = (
                    select(DocumentChunk, distance_expr.label("distance"))
                    .where(DocumentChunk.session_id == session_id)
                    .order_by(distance_expr)
                    .limit(k)
                )
                result = await db.execute(stmt)
                rows = result.all()
                
            docs_with_score = []
            for chunk, distance in rows:
                doc = Document(
                    page_content=chunk.content,
                    metadata={
                        "name": chunk.name,
                        "type": chunk.type,
                        "file_path": chunk.file_path,
                        "session_id": chunk.session_id
                    }
                )
                docs_with_score.append((doc, float(distance)))
            return docs_with_score
        except Exception as e:
            print(f"Error in retrieve_with_scores: {e}")
            return []

    async def get_relevant_documents(self, query: str, session_id: str, k: int = 8) -> List[Document]:
        return await self.retrieve(query, session_id, k)