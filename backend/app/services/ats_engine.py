import re
from dataclasses import dataclass

@dataclass
class ATSResult:
    keyword_score: float
    semantic_score: float
    experience_score: float
    completeness_score: float
    overall_score: float
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    strengths: list[str]
    concerns: list[str]
    recommendation: str

def contains_skill(text: str, skill: str) -> bool:
    value = skill.strip().casefold()
    return bool(value) and value in text.casefold()

def years_in_text(text: str) -> float:
    values = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)", text.casefold())
    return max((float(x) for x in values), default=0.0)

def calculate_ats(resume_text, required_skills, preferred_skills, min_experience_years, section_count):
    required = [x.strip() for x in required_skills if x.strip()]
    preferred = [x.strip() for x in preferred_skills if x.strip()]
    matched_required = [x for x in required if contains_skill(resume_text, x)]
    missing_required = [x for x in required if x not in matched_required]
    matched_preferred = [x for x in preferred if contains_skill(resume_text, x)]

    required_ratio = len(matched_required) / len(required) if required else 1
    preferred_ratio = len(matched_preferred) / len(preferred) if preferred else 1
    keyword_score = round(required_ratio * 80 + preferred_ratio * 20, 2)

    # Phase 3 deterministic semantic proxy. Replace with local embeddings in the next iteration.
    semantic_score = round(min(100, keyword_score * 0.9 + min(len(resume_text) / 5000, 1) * 10), 2)

    detected = years_in_text(resume_text)
    if min_experience_years is None or min_experience_years == 0:
        experience_score = 100
    else:
        experience_score = round(min(100, detected / min_experience_years * 100), 2)

    completeness_score = round(min(100, section_count / 5 * 100), 2)
    overall = round(keyword_score * .45 + semantic_score * .25 + experience_score * .20 + completeness_score * .10, 2)

    strengths = []
    concerns = []
    if matched_required:
        strengths.append(f"Matched {len(matched_required)} of {len(required)} required skills.")
    if matched_preferred:
        strengths.append(f"Matched {len(matched_preferred)} preferred skills.")
    if completeness_score >= 80:
        strengths.append("Resume contains standard sections.")
    if missing_required:
        concerns.append("Missing required skills: " + ", ".join(missing_required))
    if min_experience_years and detected < min_experience_years:
        concerns.append(f"Detected about {detected:g} years against a {min_experience_years}+ year requirement.")
    if completeness_score < 60:
        concerns.append("Several standard resume sections were not detected.")

    recommendation = "STRONG_MATCH" if overall >= 80 and not missing_required else "REVIEW" if overall >= 65 else "LOW_MATCH"
    return ATSResult(keyword_score, semantic_score, experience_score, completeness_score, overall,
                     matched_required, missing_required, matched_preferred, strengths, concerns, recommendation)
