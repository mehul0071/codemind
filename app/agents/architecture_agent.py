from app.agents.state import AgentState
from app.llm.client import client, model_name
from app.llm.prompts import ANALYZER_SYSTEM_PROMPT
from typing import Dict, Any


async def analyzer_agent(state: AgentState) -> Dict[str, Any]:
    context_str = "\n\n".join(state.get("retrieved_context", []))
    user_content = f"User Request: {state['query']}\n\nRetrieved Code Context:\n{context_str}"
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": ANALYZER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2,
        max_tokens=1024
    )
    
    analysis = response.choices[0].message.content.strip()
    return {
        "analysis": analysis
    }
