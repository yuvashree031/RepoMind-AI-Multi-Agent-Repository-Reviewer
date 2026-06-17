from langgraph.graph import StateGraph, END
from backend.agents.state import AgentState
from backend.agents.agents import (
    repository_agent,
    code_review_agent,
    security_agent,
    architecture_agent,
    devops_agent,
    report_agent
)

def create_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("repository", repository_agent)
    workflow.add_node("code_review", code_review_agent)
    workflow.add_node("security", security_agent)
    workflow.add_node("architecture", architecture_agent)
    workflow.add_node("devops", devops_agent)
    workflow.add_node("report", report_agent)

    workflow.set_entry_point("repository")

    workflow.add_edge("repository", "code_review")
    workflow.add_edge("repository", "security")
    workflow.add_edge("repository", "architecture")
    workflow.add_edge("repository", "devops")

    workflow.add_edge("code_review", "report")
    workflow.add_edge("security", "report")
    workflow.add_edge("architecture", "report")
    workflow.add_edge("devops", "report")

    workflow.add_edge("report", END)

    return workflow.compile()

workflow_app = create_workflow()
