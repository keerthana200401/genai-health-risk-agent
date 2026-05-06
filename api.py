from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from utils.rules import generate_risk_flags
from utils.validators import validate_patient_data
from utils.formatter import split_output_sections
from utils.data_loader import load_cardio_data, row_to_patient_data
from crew.health_crew import build_health_crew

load_dotenv()

app = FastAPI(
    title="Clinical Alert API",
    description="Backend service for chronic disease early warning alerts and multi-agent clinical reasoning.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PatientData(BaseModel):
    patient_id: int = 0
    age: float
    gender: str
    height_cm: float
    weight_kg: float
    bmi: float
    systolic_bp: int
    diastolic_bp: int
    glucose: int
    cholesterol: int
    smoking: str
    alcohol: str
    physical_activity: str
    heart_disease_label: int = 0


@app.get("/")
def root():
    return {
        "message": "Clinical Alert API is running",
        "docs": "http://127.0.0.1:8000/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "clinical-alert-api",
        "version": "1.0.0",
    }


@app.get("/patients")
def get_patients(limit: int = Query(50, ge=1, le=500)):
    df = load_cardio_data("data/cardio_train.csv")
    sample = df.head(limit)

    patients = []
    for _, row in sample.iterrows():
        patients.append(row_to_patient_data(row))

    return {
        "success": True,
        "count": len(patients),
        "patients": patients,
    }


@app.post("/analyze-preview")
def analyze_preview(data: PatientData):
    patient_data = data.model_dump()

    errors = validate_patient_data(patient_data)
    if errors:
        return {
            "success": False,
            "mode": "preview",
            "errors": errors,
        }

    grounded_flags = generate_risk_flags(patient_data)

    return {
        "success": True,
        "mode": "preview",
        "patient_data": patient_data,
        "grounded_flags": grounded_flags,
        "ai_output": {
            "risk_assessment": "",
            "key_factors": "",
            "doctor_warning": grounded_flags["doctor_warning"],
            "recommendations": "",
            "clinician_summary": "",
            "patient_summary": "",
            "raw_output": "",
        },
    }


@app.post("/analyze")
def analyze_patient(data: PatientData):
    patient_data = data.model_dump()

    errors = validate_patient_data(patient_data)
    if errors:
        return {
            "success": False,
            "mode": "full_ai",
            "errors": errors,
        }

    grounded_flags = generate_risk_flags(patient_data)

    ai_output = {
        "risk_assessment": "",
        "key_factors": "",
        "doctor_warning": grounded_flags["doctor_warning"],
        "recommendations": "",
        "clinician_summary": "",
        "patient_summary": "",
        "raw_output": "",
    }

    try:
        crew = build_health_crew(patient_data)
        result = crew.kickoff()

        raw_text = result.raw if hasattr(result, "raw") else str(result)
        sections = split_output_sections(raw_text)

        ai_output = {
            "risk_assessment": sections.get("risk_assessment", ""),
            "key_factors": sections.get("key_factors", ""),
            "doctor_warning": sections.get("doctor_warning", "") or grounded_flags["doctor_warning"],
            "recommendations": sections.get("recommendations", ""),
            "clinician_summary": sections.get("clinician_summary", ""),
            "patient_summary": sections.get("patient_summary", ""),
            "raw_output": raw_text,
        }

    except Exception as e:
        ai_output["raw_output"] = f"AI analysis failed: {str(e)}"

    return {
        "success": True,
        "mode": "full_ai",
        "patient_data": patient_data,
        "grounded_flags": grounded_flags,
        "ai_output": ai_output,
    }


@app.get("/batch-analyze")
def batch_analyze(limit: int = Query(50, ge=1, le=500)):
    df = load_cardio_data("data/cardio_train.csv")
    sample = df.head(limit)

    results = []

    for _, row in sample.iterrows():
        patient_data = row_to_patient_data(row)
        errors = validate_patient_data(patient_data)

        if errors:
            results.append({
                "success": False,
                "patient_data": patient_data,
                "errors": errors,
            })
            continue

        grounded_flags = generate_risk_flags(patient_data)

        results.append({
            "success": True,
            "patient_data": patient_data,
            "grounded_flags": grounded_flags,
        })

    high_count = sum(
        1 for item in results
        if item.get("success") and item["grounded_flags"]["alert_level"] == "High Risk Alert"
    )

    moderate_count = sum(
        1 for item in results
        if item.get("success") and item["grounded_flags"]["alert_level"] == "Moderate Risk Alert"
    )

    low_count = sum(
        1 for item in results
        if item.get("success") and item["grounded_flags"]["alert_level"] == "No Immediate Alert"
    )

    valid_results = [item for item in results if item.get("success")]

    avg_severity = 0
    if valid_results:
        avg_severity = round(
            sum(item["grounded_flags"]["severity_score"] for item in valid_results) / len(valid_results),
            2,
        )

    return {
        "success": True,
        "mode": "batch_preview",
        "count": len(results),
        "valid_count": len(valid_results),
        "summary": {
            "high_risk": high_count,
            "moderate_risk": moderate_count,
            "low_risk": low_count,
            "average_severity": avg_severity,
        },
        "results": results,
    }