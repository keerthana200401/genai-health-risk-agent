import os
from crewai import Crew, Task, Process, LLM

from agents.reasoning_agent import create_reasoning_agent
from agents.recommendation_agent import create_recommendation_agent
from agents.summary_agent import create_summary_agent
from utils.rules import generate_risk_flags


def build_health_crew(patient_data):
    anthropic_model = os.getenv(
    "ANTHROPIC_MODEL",
    "claude-haiku-4-5-20251001"
)

    llm = LLM(
    model=anthropic_model,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    temperature=0.1,
    )

    grounded_flags = generate_risk_flags(patient_data)

    reasoning_agent = create_reasoning_agent(llm)
    recommendation_agent = create_recommendation_agent(llm)
    summary_agent = create_summary_agent(llm)

    shared_context = f"""
Patient data:
{patient_data}

Grounded alert layer:
{grounded_flags}

Important constraints:
- This is an early warning support workflow
- Do NOT diagnose disease
- Do NOT prescribe medication
- Use only provided data
"""

    reasoning_task = Task(
        description=shared_context + """
Generate:

## Risk Assessment
- Diabetes: Low/Moderate/High
- Hypertension: Low/Moderate/High
- Heart Disease: Low/Moderate/High

## Key Factors
- factor 1
- factor 2

## Doctor Warning
Short clinician warning.
""",
        expected_output="Risk assessment with warning.",
        agent=reasoning_agent,
    )

    recommendation_task = Task(
        description=shared_context + """
Generate:

## Recommendations

### Lifestyle
- ...

### Monitoring
- ...

### Clinician Follow-up
- ...
""",
        expected_output="Recommendations.",
        agent=recommendation_agent,
        context=[reasoning_task],
    )

    summary_task = Task(
        description=shared_context + """
Generate:

## Clinician Summary
...

## Patient Summary
...
""",
        expected_output="Two summaries.",
        agent=summary_agent,
        context=[reasoning_task, recommendation_task],
    )

    crew = Crew(
        agents=[
            reasoning_agent,
            recommendation_agent,
            summary_agent
        ],
        tasks=[
            reasoning_task,
            recommendation_task,
            summary_task
        ],
        process=Process.sequential,
        verbose=False,
    )

    return crew