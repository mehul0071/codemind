from app.agents.state import AgentState
from app.llm.client import client, model_name
from app.llm.prompts import REVIEWER_SYSTEM_PROMPT
from typing import Dict, Any


async def reviewer_agent(state: AgentState) -> Dict[str, Any]:
    context_str = "\n\n".join(state.get("retrieved_context", []))
    patch_str = state.get("generated_patch") or "None"
    lint_results = state.get("lint_results")
    test_results = state.get("test_results")
    
    lint_failed = False
    lint_feedback = ""
    if lint_results and not lint_results.get("success", True):
        lint_failed = True
        errors_str = "\n".join(lint_results.get("errors", []))
        lint_feedback = (
            f"SYNTAX CHECK FAILURE:\n"
            f"The generated patch failed the automated syntax/compilation check. "
            f"Please fix the following syntax errors:\n{errors_str}"
        )
        
    if lint_failed:
        return {
            "review_feedback": lint_feedback,
            "is_complete": False
        }
        
    test_failed = False
    test_feedback = ""
    if test_results and not test_results.get("success", True):
        test_failed = True
        test_feedback = (
            f"UNIT TEST EXECUTION FAILURE:\n"
            f"The generated patch failed the automated sandboxed unit tests. "
            f"Please fix the test failures shown below:\n{test_results.get('output', '')}"
        )
        
    if test_failed:
        return {
            "review_feedback": test_feedback,
            "is_complete": False
        }
        
    lint_str = ""
    if lint_results:
        warnings = lint_results.get("errors", [])
        if warnings:
            warnings_str = "\n".join(warnings)
            lint_str = f"\n\nAutomated Linter/Formatting Warnings:\n{warnings_str}"
            
    test_str = ""
    if test_results:
        test_str = f"\n\nAutomated Test Execution Output:\n{test_results.get('output', '')}"
            
    user_content = (
        f"User Request: {state['query']}\n\n"
        f"Retrieved Code Context:\n{context_str}\n\n"
        f"Proposed Code Patch:\n{patch_str}"
        f"{lint_str}"
        f"{test_str}"
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
