import pandas as pd


def load_cardio_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath, sep=";")

    if "age" in df.columns:
        # dataset often stores age in days
        if df["age"].max() > 200:
            df["age"] = (df["age"] / 365.25).round(1)

    if "gender" in df.columns:
        df["gender"] = df["gender"].map({1: "Female", 2: "Male"}).fillna(df["gender"])

    if "smoke" in df.columns:
        df["smoking"] = df["smoke"].map({0: "Non-smoker", 1: "Smoker"})

    if "alco" in df.columns:
        df["alcohol"] = df["alco"].map({0: "Non-drinker", 1: "Drinker"})

    if "active" in df.columns:
        df["physical_activity"] = df["active"].map({0: "Low", 1: "Active"})

    if "height" in df.columns:
        df["height_cm"] = df["height"]

    if "weight" in df.columns:
        df["weight_kg"] = df["weight"]

    if "height_cm" in df.columns and "weight_kg" in df.columns:
        df["bmi"] = (df["weight_kg"] / ((df["height_cm"] / 100) ** 2)).round(1)

    if "cardio" in df.columns:
        df["heart_disease_label"] = df["cardio"]

    return df


def row_to_patient_data(row) -> dict:
    return {
        "patient_id": int(row.get("id", 0)),
        "age": float(row.get("age", 0)),
        "gender": row.get("gender", "Unknown"),
        "height_cm": float(row.get("height_cm", row.get("height", 0))),
        "weight_kg": float(row.get("weight_kg", row.get("weight", 0))),
        "bmi": float(row.get("bmi", 0)),
        "systolic_bp": int(row.get("ap_hi", row.get("systolic_bp", 0))),
        "diastolic_bp": int(row.get("ap_lo", row.get("diastolic_bp", 0))),
        "glucose": int(row.get("gluc", row.get("glucose", 1))),
        "cholesterol": int(row.get("cholesterol", 1)),
        "smoking": row.get("smoking", "Non-smoker"),
        "alcohol": row.get("alcohol", "Non-drinker"),
        "physical_activity": row.get("physical_activity", "Low"),
        "heart_disease_label": int(row.get("heart_disease_label", row.get("cardio", 0))),
    }