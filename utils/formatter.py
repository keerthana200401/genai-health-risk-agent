import re


def split_output_sections(text: str) -> dict:
    sections = {
        "risk_assessment": "",
        "key_factors": "",
        "doctor_warning": "",
        "recommendations": "",
        "clinician_summary": "",
        "patient_summary": "",
    }

    heading_map = {
        "risk assessment": "risk_assessment",
        "key factors": "key_factors",
        "doctor warning": "doctor_warning",
        "recommendations": "recommendations",
        "clinician summary": "clinician_summary",
        "patient summary": "patient_summary",
    }

    pattern = r"##\s*(.+?)\n"
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))

    for i, match in enumerate(matches):
        raw_heading = match.group(1).strip().lower().replace(":", "")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        if raw_heading in heading_map:
            sections[heading_map[raw_heading]] = content

    return sections


def alert_emoji(alert_level: str) -> str:
    level = alert_level.lower()
    if "high" in level:
        return "🔴"
    if "moderate" in level:
        return "🟠"
    return "🟢"