import re

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)

ALIASES = {
    "summary": {"summary", "professional summary", "profile", "objective"},
    "experience": {"experience", "work experience", "professional experience", "employment"},
    "education": {"education", "academic background"},
    "skills": {"skills", "technical skills", "core skills", "technologies"},
    "projects": {"projects", "personal projects", "academic projects"},
    "certifications": {"certifications", "certificates"},
}

def redact_pii(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    text = PHONE_RE.sub("[PHONE_REDACTED]", text)
    text = URL_RE.sub("[URL_REDACTED]", text)
    return text[:100000]

def extract_sections(text: str) -> dict[str, str]:
    sections = {"other": []}
    current = "other"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        key = re.sub(r"[^a-z ]", "", line.casefold()).strip()
        match = next((name for name, aliases in ALIASES.items() if key in aliases), None)
        if match:
            current = match
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v) for k, v in sections.items() if v}
