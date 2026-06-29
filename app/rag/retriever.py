from typing import List, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings
import chromadb
import os


class CodeRetriever:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )
        os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        self.collection_name = "codemind_codebase"

    def _get_vectorstore(self, session_id: str = None) -> Chroma:
        return Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

    async def retrieve(self, query: str, session_id: str, k: int = 8) -> List[Document]:
        try:
            vectorstore = self._get_vectorstore()            
            docs = vectorstore.similarity_search(
                query=query,
                k=k,
                filter={"session_id": session_id}
            )
            
            return docs
            
        except Exception as e:
            print(f"Error in retrieve: {e}")
            return []

    async def retrieve_with_scores(self, query: str, session_id: str, k: int = 8) -> List[Tuple[Document, float]]:
        try:
            vectorstore = self._get_vectorstore()
            docs_with_score = vectorstore.similarity_search_with_score(
                query=query,
                k=k,
                filter={"session_id": session_id}
            )
            
            return docs_with_score
            
        except Exception as e:
            print(f"Error in retrieve_with_scores: {e}")
            return []

    async def get_relevant_documents(self, query: str, session_id: str, k: int = 8) -> List[Document]:
        return await self.retrieve(query, session_id, k)