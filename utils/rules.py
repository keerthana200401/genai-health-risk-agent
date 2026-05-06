def category_label(value: int) -> str:
    mapping = {
        1: "Normal",
        2: "Above Normal",
        3: "Well Above Normal"
    }
    return mapping.get(int(value), "Unknown")


def score_to_label(score: float, moderate_cutoff: float, high_cutoff: float) -> str:
    if score >= high_cutoff:
        return "High"
    if score >= moderate_cutoff:
        return "Moderate"
    return "Low"


def generate_risk_flags(patient_data: dict) -> dict:
    """
    Grounded rule-based early warning layer.
    This does not diagnose disease.
    """

    age = float(patient_data.get("age", 0))
    bmi = float(patient_data.get("bmi", 0))
    systolic = int(patient_data.get("systolic_bp", 0))
    diastolic = int(patient_data.get("diastolic_bp", 0))
    glucose = int(patient_data.get("glucose", 1))
    cholesterol = int(patient_data.get("cholesterol", 1))
    smoking = patient_data.get("smoking", "Non-smoker")
    alcohol = patient_data.get("alcohol", "Non-drinker")
    activity = patient_data.get("physical_activity", "Low")

    notes = []
    contributors = []

    diabetes_score = 0.0
    hypertension_score = 0.0
    heart_score = 0.0

    # ---------- Diabetes-oriented risk ----------
    if glucose == 3:
        diabetes_score += 3
        notes.append("Glucose is well above normal.")
        contributors.append("Very high glucose")
    elif glucose == 2:
        diabetes_score += 2
        notes.append("Glucose is above normal.")
        contributors.append("High glucose")

    if bmi >= 30:
        diabetes_score += 2
        notes.append("BMI is in the obesity range.")
        contributors.append("Obesity")
    elif bmi >= 25:
        diabetes_score += 1
        notes.append("BMI is in the overweight range.")
        contributors.append("Overweight")

    if age >= 45:
        diabetes_score += 1
        notes.append("Age adds metabolic risk.")

    # ---------- Hypertension-oriented risk ----------
    if systolic >= 140 or diastolic >= 90:
        hypertension_score += 3
        notes.append("Blood pressure is in a high range.")
        contributors.append("High blood pressure")
    elif systolic >= 130 or diastolic >= 85:
        hypertension_score += 2
        notes.append("Blood pressure is borderline elevated.")
        contributors.append("Elevated blood pressure")
    elif systolic >= 120:
        hypertension_score += 1

    if bmi >= 30:
        hypertension_score += 1
    elif bmi >= 25:
        hypertension_score += 0.5

    if activity == "Low":
        hypertension_score += 1
        notes.append("Low physical activity may contribute to blood pressure risk.")
        contributors.append("Low physical activity")

    # ---------- Heart disease-oriented risk ----------
    if age >= 50:
        heart_score += 2
        notes.append("Age contributes to cardiovascular risk.")
        contributors.append("Older age")
    elif age >= 40:
        heart_score += 1

    if cholesterol == 3:
        heart_score += 3
        notes.append("Cholesterol is well above normal.")
        contributors.append("Very high cholesterol")
    elif cholesterol == 2:
        heart_score += 2
        notes.append("Cholesterol is above normal.")
        contributors.append("High cholesterol")

    if smoking == "Smoker":
        heart_score += 2
        notes.append("Smoking increases cardiovascular risk.")
        contributors.append("Smoking")

    if systolic >= 140 or diastolic >= 90:
        heart_score += 2
    elif systolic >= 130 or diastolic >= 85:
        heart_score += 1

    if bmi >= 30:
        heart_score += 1
    elif bmi >= 25:
        heart_score += 0.5

    if activity == "Low":
        heart_score += 1

    if alcohol == "Drinker":
        heart_score += 0.5

    # ---------- Convert to labels ----------
    diabetes_flag = score_to_label(diabetes_score, moderate_cutoff=2, high_cutoff=5)
    hypertension_flag = score_to_label(hypertension_score, moderate_cutoff=2, high_cutoff=5)
    heart_disease_flag = score_to_label(heart_score, moderate_cutoff=3, high_cutoff=6)

    # ---------- Overall severity ----------
    total_score = diabetes_score + hypertension_score + heart_score
    severity_score = min(int(total_score * 7), 100)

    contributor_count = len(set(contributors))
    confidence = min(60 + contributor_count * 5, 95)

    if severity_score >= 70:
        alert_level = "High Risk Alert"
        alert_color = "red"
        doctor_warning = (
            f"Overall severity score is {severity_score}/100. Multiple chronic disease "
            f"warning indicators are elevated. Early clinical review and preventive follow-up are recommended."
        )
    elif severity_score >= 40:
        alert_level = "Moderate Risk Alert"
        alert_color = "orange"
        doctor_warning = (
            f"Overall severity score is {severity_score}/100. Some important warning indicators "
            f"are present. Preventive monitoring and clinician attention are advisable."
        )
    else:
        alert_level = "No Immediate Alert"
        alert_color = "green"
        doctor_warning = (
            f"Overall severity score is {severity_score}/100. No strong immediate alert was triggered "
            f"from the available indicators, but routine monitoring should continue."
        )

    return {
        "diabetes_flag": diabetes_flag,
        "hypertension_flag": hypertension_flag,
        "heart_disease_flag": heart_disease_flag,
        "alert_level": alert_level,
        "alert_color": alert_color,
        "doctor_warning": doctor_warning,
        "severity_score": severity_score,
        "confidence": confidence,
        "contributors": list(dict.fromkeys(contributors)),
        "notes": list(dict.fromkeys(notes)),
        "glucose_text": category_label(glucose),
        "cholesterol_text": category_label(cholesterol),
    }