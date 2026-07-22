import asyncio
from typing import List, Tuple
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from app.utils.helpers import logger


class CodeReranker:

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            try:
                self._model = CrossEncoder(self.model_name)
                logger.info(f"[CodeReranker] Loaded cross-encoder: {self.model_name}")
            except Exception as e:
                logger.error(f"[CodeReranker] Failed to load cross-encoder: {e}. Reranking disabled.")
                self._model = None
        return self._model

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_n: int = 8,
    ) -> List[Document]:

        if not documents:
            return documents

        model = self._load_model()
        if model is None:
            return documents[:top_n]

        pairs = [(query, doc.page_content) for doc in documents]
        scores: List[float] = await asyncio.to_thread(model.predict, pairs)

        scored = sorted(
            zip(scores, documents),
            key=lambda x: x[0],
            reverse=True,
        )

        reranked = [doc for _, doc in scored[:top_n]]
        return reranked

    async def rerank_with_scores(
        self,
        query: str,
        documents: List[Document],
        top_n: int = 8,
    ) -> List[Tuple[Document, float]]:
        """Same as rerank() but returns (document, score) tuples."""
        if not documents:
            return []

        model = self._load_model()
        if model is None:
            return [(doc, 0.0) for doc in documents[:top_n]]

        pairs = [(query, doc.page_content) for doc in documents]
        scores: List[float] = await asyncio.to_thread(model.predict, pairs)

        scored = sorted(
            zip(scores, documents),
            key=lambda x: x[0],
            reverse=True,
        )

        return [(doc, float(score)) for score, doc in scored[:top_n]]
