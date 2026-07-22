from typing import Dict, List, Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.rag.retriever import CodeRetriever
from app.rag.prompts import get_system_prompt, get_query_prompt
from app.config import settings
from app.utils.helpers import logger
from app.db.sessions import AsyncSessionLocal
from app.db.models.repository import Repository
from sqlalchemy import select
from groq import Groq
import json


class RetrievalService:
    def __init__(self):
        self.retriever = CodeRetriever()
        self.llm_client = Groq(api_key=settings.GROQ_API_KEY)
        self.model_name = settings.MODEL_NAME

    def _format_context(self, documents: List[Any]) -> str:
        context_parts = []
        
        for i, doc in enumerate(documents):
            file_path = doc.metadata.get("file_path", "unknown")
            content = doc.page_content
            
            part = f"""--- Source {i+1}: {file_path} ---
                    {content}
                    """
            context_parts.append(part)
        
        return "\n".join(context_parts)

    async def get_answer(self, query: str, session_id: str, user_id: str) -> Dict[str, Any]:
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(Repository).where(
                    Repository.session_id == session_id,
                    Repository.user_id == user_id
                )
                result = await db.execute(stmt)
                if not result.scalar_one_or_none():
                    return {
                        "answer": "Unauthorized or repository not found.",
                        "sources": [],
                        "success": False,
                        "num_sources": 0,
                    }

            documents = await self.retriever.retrieve(
                query=query,
                session_id=session_id,
                k=7
            )

            if not documents:
                return {
                    "answer": "I couldn't find any relevant code for this query in the provided codebase.",
                    "sources": [],
                    "success": False,
                    "num_sources": 0,
                }

            context = self._format_context(documents)
            system_prompt = get_system_prompt()
            final_prompt = get_query_prompt(query, context)

            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.3,
                max_tokens=1024,
            )

            answer = response.choices[0].message.content.strip()
            sources = [
                {
                    "file_path": doc.metadata.get("file_path"),
                    "type": doc.metadata.get("type", "unknown"),
                    "name": doc.metadata.get("name", "")
                }
                for doc in documents
            ]

            return {
                "answer": answer,
                "sources": sources,
                "success": True,
                "num_sources": len(documents)
            }

        except Exception as e:
            logger.error(f"Error in get_answer: {e}")
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": [],
                "success": False,
                "num_sources": 0,
            }


    async def get_answer_with_citations(self, query: str, session_id: str) -> Dict[str, Any]:
        try:
            documents = await self.retriever.retrieve(query, session_id, k=8)
            
            if not documents:
                return {"answer": "No relevant context found.", "citations": [], "success": False}

            context = self._format_context(documents)
            system_prompt = get_system_prompt()
            enhanced_prompt = f"""
                {get_query_prompt(query, context)}
                Please format your response as JSON with:
                {{
                "answer": "your detailed answer here",
                "citations": ["file_path1", "file_path2"]
                }}
            """

            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                temperature=0.2,
                max_tokens=1200,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            return {
                "answer": result.get("answer", ""),
                "citations": result.get("citations", []),
                "success": True
            }

        except Exception as e:
            logger.error(f"Error in get_answer_with_citations: {e}")
            return {"answer": "Error generating structured response", "citations": [], "success": False}