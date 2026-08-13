import json
import os

SYSTEM_PROMPT = """You are a recruitment screening explainability layer.
Use only job-relevant evidence. Never infer or score age, gender, race, religion,
nationality, health, photo, name, address, or other protected characteristics.
Do not invent skills or experience. Return JSON with strengths, concerns,
improvement_suggestions, and explanation."""

def fallback(base):
    return {
        "strengths": base["strengths"][:5],
        "concerns": base["concerns"][:5],
        "improvement_suggestions": [
            "Add concrete evidence for missing required skills where applicable.",
            "Quantify impact in experience and project descriptions.",
            "Use standard section headings for reliable machine parsing.",
        ],
        "explanation": f"The deterministic screening score is {base['overall_score']:.1f}/100. It is a screening aid, not a hiring decision.",
    }

def explain(base, job_description, resume_text):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return fallback(base), "deterministic", "none"
    try:
        from google import genai
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            contents=SYSTEM_PROMPT + "\nJOB:\n" + job_description[:20000] + "\nRESUME:\n" + resume_text[:30000] + "\nBASELINE:\n" + json.dumps(base),
            config={"response_mime_type": "application/json"},
        )
        parsed = json.loads(response.text or "{}")
        return {
            "strengths": parsed.get("strengths", base["strengths"])[:5],
            "concerns": parsed.get("concerns", base["concerns"])[:5],
            "improvement_suggestions": parsed.get("improvement_suggestions", [])[:5],
            "explanation": str(parsed.get("explanation", ""))[:4000],
        }, "gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    except Exception:
        return fallback(base), "deterministic", "none"
