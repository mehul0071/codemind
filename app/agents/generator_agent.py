from app.agents.state import AgentState
from app.llm.client import client, model_name
from app.llm.prompts import GENERATOR_SYSTEM_PROMPT
from typing import Dict, Any


async def generator_agent(state: AgentState) -> Dict[str, Any]:
    context_str = "\n\n".join(state.get("retrieved_context", []))
    analysis_str = state.get("analysis") or "No architectural analysis available."
    current_iterations = state.get("iteration_count", 0)

    sections = [
        f"User Request: {state['query']}",
        f"Architectural Analysis:\n{analysis_str}",
        f"Retrieved Code Context:\n{context_str}",
    ]

    review_feedback = state.get("review_feedback")
    lint_results = state.get("lint_results")
    test_results = state.get("test_results")

    if current_iterations > 0:
        sections.append(
            "--- PREVIOUS ATTEMPT FAILED — FIX THE ISSUES BELOW ---\n"
            "Your previous code generation was rejected. You MUST address all issues listed below "
            "before outputting the new code patch."
        )

    if review_feedback and review_feedback.strip():
        sections.append(f"Reviewer Critique:\n{review_feedback}")

    if lint_results and not lint_results.get("success", True):
        errors = "\n".join(lint_results.get("errors", []))
        sections.append(f"Linter / Compile Errors to Fix:\n{errors}")

    if test_results and not test_results.get("success", True):
        sections.append(f"Failing Unit Tests Output:\n{test_results.get('output', '')}")

    user_content = "\n\n".join(sections)

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

    return {
        "generated_patch": patch,
        "iteration_count": current_iterations + 1,
    }