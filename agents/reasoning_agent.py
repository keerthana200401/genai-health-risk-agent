from crewai import Agent
from rag_pipeline import retrieve_similar

def create_reasoning_agent(llm):
    return Agent(
        role="Clinical Risk Reasoning Agent",
        goal=(
            "Assess likely early warning risk levels for diabetes, hypertension, and "
            "heart disease using only structured patient indicators and grounded rule outputs."
        ),
        backstory=(
            "You are a clinical decision-support reasoning specialist. You do not diagnose disease. "
            "You identify likely preventive risk levels and explain the strongest contributing factors "
            "in a concise, professional tone."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

def get_rag_context(patient_text):
    """Retrieve similar patient cases from Pinecone"""
    similar_cases = retrieve_similar(patient_text, top_k=3)
    context = "\n".join([f"- {case}" for case in similar_cases])
    return f"Similar patient cases from records:\n{context}"