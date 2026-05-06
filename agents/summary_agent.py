from crewai import Agent


def create_summary_agent(llm):
    return Agent(
        role="Clinical Summary Agent",
        goal=(
            "Produce clear clinician-facing and patient-friendly summaries for an early warning "
            "clinical decision-support system."
        ),
        backstory=(
            "You specialize in translating grounded risk signals into concise summaries for different audiences. "
            "Your language is clear, preventive, and non-diagnostic."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )