from app.agents.state import AgentState
from app.llm.client import client, model_name
from app.llm.prompts import GENERATOR_SYSTEM_PROMPT
from typing import Dict, Any


async def generator_agent(state: AgentState) -> Dict[str, Any]:
    context_str = "\n\n".join(state.get("retrieved_context", []))
    analysis_str = state.get("analysis") or "None"
    feedback_str = state.get("review_feedback") or "None"
    lint_str = str(state.get("lint_results")) if state.get("lint_results") else "None"
    
    user_content = (
        f"User Request: {state['query']}\n\n"
        f"Architectural Analysis:\n{analysis_str}\n\n"
        f"Retrieved Code Context:\n{context_str}\n\n"
        f"Previous Reviewer Feedback:\n{feedback_str}\n\n"
        f"Previous Linter/Compile Results:\n{lint_str}"
    )
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": GENERATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2,
        max_tokens=2048
    )
    
    patch = response.choices[0].message.content.strip()
    current_iterations = state.get("iteration_count", 0)
    
    return {
        "generated_patch": patch,
        "iteration_count": current_iterations + 1
    }
