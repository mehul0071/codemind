import chromadb
from chromadb.utils import embedding_functions
from app.config import settings
from langchain_core.documents import Document
from typing import List


class ChromaVectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.VECTOR_DB_PATH)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
    
    def get_or_create_collection(self, session_id: str):
        collection_name = f"session_{session_id}"
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: List[Document], session_id: str) -> int:
        if not documents:
            return 0
            
        collection = self.get_or_create_collection(session_id)
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [f"chunk_{i}_{session_id}" for i in range(len(documents))]
        
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        return len(documents)
    
    def get_collection(self, session_id: str):
        collection_name = f"session_{session_id}"
        try:
            return self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
        except Exception:
            return None