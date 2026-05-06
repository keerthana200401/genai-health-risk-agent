from crewai import Agent


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