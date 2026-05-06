def validate_patient_data(patient_data: dict) -> list[str]:
    errors = []

    age = patient_data.get("age", 0)
    bmi = patient_data.get("bmi", 0)
    systolic = patient_data.get("systolic_bp", 0)
    diastolic = patient_data.get("diastolic_bp", 0)
    glucose = patient_data.get("glucose", 1)
    cholesterol = patient_data.get("cholesterol", 1)

    if not (0 < age <= 120):
        errors.append("Age must be between 1 and 120.")

    if not (10 <= bmi <= 80):
        errors.append("BMI appears out of valid range.")

    if not (50 <= systolic <= 250):
        errors.append("Systolic blood pressure appears out of valid range.")

    if not (30 <= diastolic <= 150):
        errors.append("Diastolic blood pressure appears out of valid range.")

    if glucose not in [1, 2, 3]:
        errors.append("Glucose category must be 1, 2, or 3.")

    if cholesterol not in [1, 2, 3]:
        errors.append("Cholesterol category must be 1, 2, or 3.")

    return errors