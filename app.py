import streamlit as st
from dotenv import load_dotenv
from graph.health_graph import build_health_graph
from utils.data_loader import load_cardio_data, row_to_patient_data
from utils.rules import generate_risk_flags
from utils.formatter import split_output_sections, alert_emoji
from utils.validators import validate_patient_data

load_dotenv()

st.set_page_config(
    page_title="AI-Powered Multi-Agent Clinical Early Warning System",
    layout="wide"
)

st.title("AI-Powered Multi-Agent Clinical Early Warning System")
st.caption("Generative AI-based preventive decision support for chronic disease risk alerts")

df = load_cardio_data("data/cardio_train.csv")

st.sidebar.header("Patient Source")
st.sidebar.caption("Powered by CrewAI + Ollama + Streamlit")

source_mode = st.sidebar.radio(
    "Choose input type",
    ["Select from dataset", "Manual entry"]
)

if source_mode == "Select from dataset":
    st.sidebar.subheader("Dataset Patient Selection")
    selected_index = st.sidebar.number_input(
        "Row index",
        min_value=0,
        max_value=len(df) - 1,
        value=0,
        step=1
    )
    patient_data = row_to_patient_data(df.iloc[selected_index])

else:
    st.sidebar.subheader("Manual Patient Entry")

    height_cm = st.sidebar.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=170.0)
    weight_kg = st.sidebar.number_input("Weight (kg)", min_value=30.0, max_value=250.0, value=72.0)
    bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)

    patient_data = {
        "patient_id": 0,
        "age": st.sidebar.number_input("Age", min_value=1, max_value=120, value=45),
        "gender": st.sidebar.selectbox("Gender", ["Female", "Male"]),
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
        "systolic_bp": st.sidebar.number_input("Systolic BP", min_value=50, max_value=250, value=120),
        "diastolic_bp": st.sidebar.number_input("Diastolic BP", min_value=30, max_value=150, value=80),
        "glucose": st.sidebar.selectbox(
            "Glucose Category",
            [1, 2, 3],
            format_func=lambda x: {1: "Normal", 2: "Above Normal", 3: "Well Above Normal"}[x],
        ),
        "cholesterol": st.sidebar.selectbox(
            "Cholesterol Category",
            [1, 2, 3],
            format_func=lambda x: {1: "Normal", 2: "Above Normal", 3: "Well Above Normal"}[x],
        ),
        "smoking": st.sidebar.selectbox("Smoking", ["Non-smoker", "Smoker"]),
        "alcohol": st.sidebar.selectbox("Alcohol", ["Non-drinker", "Drinker"]),
        "physical_activity": st.sidebar.selectbox("Physical Activity", ["Low", "Active"]),
        "heart_disease_label": 0,
    }

validation_errors = validate_patient_data(patient_data)
if validation_errors:
    for err in validation_errors:
        st.error(err)
    st.stop()

grounded_flags = generate_risk_flags(patient_data)

emoji = alert_emoji(grounded_flags["alert_level"])

if grounded_flags["alert_color"] == "red":
    st.error(f"{emoji} {grounded_flags['alert_level']}")
elif grounded_flags["alert_color"] == "orange":
    st.warning(f"{emoji} {grounded_flags['alert_level']}")
else:
    st.success(f"{emoji} {grounded_flags['alert_level']}")

st.info(grounded_flags["doctor_warning"])

st.subheader("Risk Severity Overview")

risk_col1, risk_col2 = st.columns(2)

with risk_col1:
    st.metric("Severity Score", f"{grounded_flags['severity_score']}/100")

with risk_col2:
    st.metric("Confidence", f"{grounded_flags['confidence']}%")

st.progress(min(grounded_flags["severity_score"], 100) / 100)

st.subheader("Patient Profile")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Age", patient_data["age"])
    st.metric("Gender", patient_data["gender"])
    st.metric("BMI", patient_data["bmi"])

with col2:
    st.metric("Systolic BP", patient_data["systolic_bp"])
    st.metric("Diastolic BP", patient_data["diastolic_bp"])
    st.metric("Glucose", grounded_flags["glucose_text"])

with col3:
    st.metric("Cholesterol", grounded_flags["cholesterol_text"])
    st.metric("Smoking", patient_data["smoking"])
    st.metric("Activity", patient_data["physical_activity"])

st.subheader("Grounded Alert Overview")

c1, c2, c3 = st.columns(3)
c1.metric("Diabetes Alert", grounded_flags["diabetes_flag"])
c2.metric("Hypertension Alert", grounded_flags["hypertension_flag"])
c3.metric("Heart Disease Alert", grounded_flags["heart_disease_flag"])

exp1, exp2 = st.columns(2)

with exp1:
    with st.expander("Why this alert was triggered", expanded=True):
        if grounded_flags["notes"]:
            for note in grounded_flags["notes"]:
                st.write(f"- {note}")
        else:
            st.write("No structured explanation available.")

with exp2:
    with st.expander("Top Contributing Factors", expanded=True):
        if grounded_flags["contributors"]:
            for item in grounded_flags["contributors"]:
                st.write(f"- {item}")
        else:
            st.write("No major contributors identified.")


def apply_safe_fallbacks(sections, grounded_flags):
    if not sections["doctor_warning"]:
        sections["doctor_warning"] = grounded_flags["doctor_warning"]

    if not sections["recommendations"]:
        sections["recommendations"] = """
- Continue routine monitoring of blood pressure, glucose, cholesterol, and BMI.
- Encourage healthy lifestyle behaviors such as regular physical activity, balanced diet, and smoking avoidance.
- Consider clinician follow-up if elevated indicators persist or risk level increases.
"""

    if not sections["clinician_summary"]:
        contributors = (
            ", ".join(grounded_flags["contributors"])
            if grounded_flags["contributors"]
            else "no major elevated indicators"
        )

        sections["clinician_summary"] = (
            f"The patient shows a {grounded_flags['alert_level'].lower()} with "
            f"a severity score of {grounded_flags['severity_score']}/100. "
            f"Key contributing factors include: {contributors}."
        )

    if not sections["patient_summary"]:
        sections["patient_summary"] = (
            "Your current health indicators suggest that routine monitoring should continue. "
            "This result does not confirm a disease, but it highlights areas that may benefit from "
            "healthy lifestyle habits and follow-up with a healthcare professional if needed."
        )

    if not sections["risk_assessment"]:
        sections["risk_assessment"] = f"""
- Diabetes: {grounded_flags['diabetes_flag']}
- Hypertension: {grounded_flags['hypertension_flag']}
- Heart Disease: {grounded_flags['heart_disease_flag']}
"""

    if not sections["key_factors"]:
        if grounded_flags["notes"]:
            sections["key_factors"] = "\n".join(
                [f"- {note}" for note in grounded_flags["notes"]]
            )
        else:
            sections["key_factors"] = "- No major elevated indicators were identified."

    return sections


if st.button("Run Clinical Alert Analysis", type="primary"):
    try:
        with st.spinner("Running multi-agent clinical reasoning..."):
            graph = build_health_graph()
            graph_result = graph.invoke({
                "patient_data": patient_data,
                "grounded_flags": grounded_flags,
                "rag_context": "",
                "risk_level": "",
                "crew_result": None
            })
            result = graph_result["crew_result"]

            if hasattr(result, "tasks_output") and result.tasks_output:
                task_texts = []
                for task_output in result.tasks_output:
                    if hasattr(task_output, "raw"):
                        task_texts.append(task_output.raw)
                    else:
                        task_texts.append(str(task_output))
                full_text = "\n\n".join(task_texts)
            else:
                full_text = result.raw if hasattr(result, "raw") else str(result)

            sections = split_output_sections(full_text)
            sections = apply_safe_fallbacks(sections, grounded_flags)

        st.divider()
        st.subheader("AI Clinical Alert Output")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Clinical Risk",
            "Triggered Factors",
            "Doctor Warning",
            "Recommendations",
            "Summaries"
        ])

        with tab1:
            st.markdown(sections["risk_assessment"])

        with tab2:
            st.markdown(sections["key_factors"])

        with tab3:
            st.markdown(sections["doctor_warning"])

        with tab4:
            st.markdown(sections["recommendations"])

        with tab5:
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("### Clinician Summary")
                st.markdown(sections["clinician_summary"])

            with col_b:
                st.markdown("### Patient Summary")
                st.markdown(sections["patient_summary"])

        with st.expander("Agent Workflow Trace"):
            st.markdown("""
1. **Grounded Rule Engine** evaluated structured patient indicators  
2. **Reasoning Agent** assessed likely risk levels and key contributing factors  
3. **Recommendation Agent** generated preventive follow-up guidance  
4. **Summary Agent** produced clinician-facing and patient-friendly summaries  
""")

        with st.expander("Raw Model Output"):
            st.text(full_text)

    except Exception as e:
        st.error("Clinical alert analysis failed.")
        st.exception(e)

st.divider()
st.subheader("Executive Dashboard")
st.caption(
    "A product-style dashboard experience for interactive chronic disease risk monitoring "
    "and clinical decision support."
)

st.success(
    "Launch the advanced dashboard experience for a product-style view of patient risk indicators "
    "and alert insights."
)

st.link_button(
    "Open Executive Dashboard",
    "http://localhost:5173"
)