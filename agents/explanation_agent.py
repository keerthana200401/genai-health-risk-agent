from crewai import Agent

def create_explanation_agent(llm):
    return Agent(
        role="Explanation Agent",
        goal="Explain contributing health risk factors clearly.",
        backstory="You explain why certain health indicators raise concern.",
        llm=llm,
        verbose=False
    )