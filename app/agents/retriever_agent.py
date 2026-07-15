from app.agents.state import AgentState
from app.rag.retriever import CodeRetriever
from typing import Dict, Any


async def retriever_agent(state: AgentState) -> Dict[str, Any]:
    retriever = CodeRetriever()
    docs = await retriever.retrieve(
        query=state["query"],
        session_id=state["session_id"]
    )
    
    retrieved_context = []
    files_retrieved = set()
    
    for doc in docs:
        retrieved_context.append(doc.page_content)
        file_path = doc.metadata.get("file_path")
        if file_path:
            files_retrieved.add(file_path)
            
    return {
        "retrieved_context": retrieved_context,
        "files_retrieved": list(files_retrieved)
    }
