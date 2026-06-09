from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
from crew.health_crew import build_health_crew
from rag_pipeline import retrieve_similar
from utils.rules import generate_risk_flags

# Define state
class PatientState(TypedDict):
    patient_data: dict
    grounded_flags: dict
    rag_context: str
    risk_level: str
    crew_result: Optional[object]

def rag_retrieval_node(state: PatientState) -> PatientState:
    """Retrieve similar patient cases from Pinecone"""
    similar_cases = retrieve_similar(str(state["patient_data"]), top_k=3)
    context = "\n".join([f"- {case}" for case in similar_cases])
    state["rag_context"] = context
    return state

def risk_assessment_node(state: PatientState) -> PatientState:
    """Determine risk level from grounded flags"""
    severity = state["grounded_flags"]["severity_score"]
    if severity >= 60:
        state["risk_level"] = "high"
    elif severity >= 30:
        state["risk_level"] = "moderate"
    else:
        state["risk_level"] = "low"
    return state

def full_analysis_node(state: PatientState) -> PatientState:
    """Run full CrewAI pipeline for high/moderate risk"""
    print(">>> FULL ANALYSIS NODE running")
    crew = build_health_crew(state["patient_data"])
    state["crew_result"] = crew.kickoff()
    return state

def summary_only_node(state: PatientState) -> PatientState:
    """Lightweight summary for low risk patients - skip full crew"""
    print(">>> SUMMARY ONLY NODE running - low risk path")
    from crewai import Crew, Task, Process, LLM
    from agents.summary_agent import create_summary_agent
    import os

    llm = LLM(
        model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        temperature=0.1,
    )

    summary_agent = create_summary_agent(llm)

    task = Task(
        description=f"""
Patient data: {state['patient_data']}
This is a LOW RISK patient. Generate only:
## Clinician Summary
Brief low-risk summary.
## Patient Summary
Reassuring patient message.
""",
        expected_output="Two brief summaries.",
        agent=summary_agent,
    )

    crew = Crew(
        agents=[summary_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False
    )
    state["crew_result"] = crew.kickoff()
    return state

def route_by_risk(state: PatientState) -> str:
    """Conditional routing based on risk level"""
    if state["risk_level"] in ["high", "moderate"]:
        return "full_analysis"
    return "summary_only"

def build_health_graph():
    graph = StateGraph(PatientState)

    # Add nodes
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("risk_assessment", risk_assessment_node)
    graph.add_node("full_analysis", full_analysis_node)
    graph.add_node("summary_only", summary_only_node)

    # Add edges
    graph.set_entry_point("rag_retrieval")
    graph.add_edge("rag_retrieval", "risk_assessment")
    graph.add_conditional_edges(
        "risk_assessment",
        route_by_risk,
        {
            "full_analysis": "full_analysis",
            "summary_only": "summary_only"
        }
    )
    graph.add_edge("full_analysis", END)
    graph.add_edge("summary_only", END)

    return graph.compile()