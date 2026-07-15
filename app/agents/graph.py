from langgraph.graph import StateGraph, START, END
from app.agents.state import AgentState
from app.agents.retriever_agent import retriever_agent
from app.agents.architecture_agent import analyzer_agent
from app.agents.generator_agent import generator_agent
from app.agents.syntax_check_agent import syntax_check_agent
from app.agents.sandbox_agent import sandbox_agent
from app.agents.review_agent import reviewer_agent


def route_after_review(state: AgentState) -> str:
    if state.get("is_complete") or state.get("iteration_count", 0) >= 3:
        return END
    return "generator"


workflow = StateGraph(AgentState)

workflow.add_node("retriever", retriever_agent)
workflow.add_node("analyzer", analyzer_agent)
workflow.add_node("generator", generator_agent)
workflow.add_node("syntax_checker", syntax_check_agent)
workflow.add_node("sandbox_runner", sandbox_agent)
workflow.add_node("reviewer", reviewer_agent)

workflow.add_edge(START, "retriever")
workflow.add_edge("retriever", "analyzer")
workflow.add_edge("analyzer", "generator")
workflow.add_edge("generator", "syntax_checker")
workflow.add_edge("syntax_checker", "sandbox_runner")
workflow.add_edge("sandbox_runner", "reviewer")

workflow.add_conditional_edges(
    "reviewer",
    route_after_review,
    {
        END: END,
        "generator": "generator"
    }
)

app_graph = workflow.compile()
