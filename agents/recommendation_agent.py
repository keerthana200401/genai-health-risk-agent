from crewai import Agent


def create_recommendation_agent(llm):
    return Agent(
        role="Preventive Recommendation Agent",
        goal=(
            "Generate concise and practical preventive recommendations for a doctor-facing "
            "clinical alert workflow."
        ),
        backstory=(
            "You support preventive care workflows. You do not diagnose or prescribe medication. "
            "You focus on monitoring, lifestyle reinforcement, and clinician follow-up actions."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )