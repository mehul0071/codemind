from app.agents.state import AgentState
from app.llm.client import client, model_name
from app.llm.prompts import REVIEWER_SYSTEM_PROMPT
from typing import Dict, Any


async def reviewer_agent(state: AgentState) -> Dict[str, Any]:
    context_str = "\n\n".join(state.get("retrieved_context", []))
    patch_str = state.get("generated_patch") or "None"
    
    user_content = (
        f"User Request: {state['query']}\n\n"
        f"Retrieved Code Context:\n{context_str}\n\n"
        f"Proposed Code Patch:\n{patch_str}"
    )
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2,
        max_tokens=1024
    )
    
    feedback = response.choices[0].message.content.strip()
    is_approved = feedback.strip().upper().startswith("APPROVED")
    
    return {
        "review_feedback": feedback,
        "is_complete": is_approved
    }
