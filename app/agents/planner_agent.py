import json
from app.agents.state import AgentState
from app.llm.client import client, model_name
from typing import Dict, Any


PLANNER_SYSTEM_PROMPT = """
    You are a code task classifier for the CodeMind agentic system.
    Given a user's request about a codebase, classify it into exactly ONE of:

    - CODE_TASK  — The user wants to generate, write, modify, refactor, fix, or add code.
    - QA_QUERY   — The user wants an explanation, description, or answer about existing code (no code generation needed).

    Reply ONLY with a valid JSON object in this exact format:
    {"task_type": "CODE_TASK", "reasoning": "short reason"}
    or
    {"task_type": "QA_QUERY", "reasoning": "short reason"}

    Do not output anything else.
"""


async def planner_agent(state: AgentState) -> Dict[str, Any]:
    query = state.get("query", "")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {"role": "user", "content": f"User request: {query}"},
            ],
            temperature=0.0,
            max_tokens=128,
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        task_type = parsed.get("task_type", "CODE_TASK")
        reasoning = parsed.get("reasoning", "")
        print(f"[PlannerAgent] Classified as '{task_type}': {reasoning}")
    except Exception as e:
        print(f"[PlannerAgent] Classification failed ({e}), defaulting to CODE_TASK")
        task_type = "CODE_TASK"

    return {"task_type": task_type}
