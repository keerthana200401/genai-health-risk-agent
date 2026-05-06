from crewai import Agent

def create_intake_agent(llm):
    return Agent(
        role="Patient Intake Agent",
        goal="Validate and summarize patient data.",
        backstory="You review structured patient health data and identify important indicators.",
        llm=llm,
        verbose=False
    )