"""Deterministic ATS (Applicant Tracking System) scoring engine.

Scores a parsed resume against a job description without calling external LLMs.
Uses strict skill matching, regex-based experience extraction, and heuristics:

- Skill matching preserves C++, .NET, C#, etc., without boundary stripping.
- Synonyms are mapped deterministically via SKILL_ALIASES.
- Experience extraction avoids false matches on company ages, product release
  dates, and historical years.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

# -----------------------------------------------------------------------------
# Score weights
#
# Named and summing to 1.0 so a change is deliberate and auditable, rather than
# magic numbers spread across two divergent copies of the pipeline.
# -----------------------------------------------------------------------------

WEIGHT_KEYWORD: Final = 0.45
WEIGHT_SEMANTIC: Final = 0.25
WEIGHT_EXPERIENCE: Final = 0.20
WEIGHT_COMPLETENESS: Final = 0.10

# Within the keyword sub-score, required skills dominate preferred ones.
REQUIRED_SKILL_WEIGHT: Final = 0.80
PREFERRED_SKILL_WEIGHT: Final = 0.20

STRONG_MATCH_THRESHOLD: Final = 80.0
REVIEW_THRESHOLD: Final = 65.0

# Canonical sections expected of a complete resume.
EXPECTED_SECTION_COUNT: Final = 5

# Characters that count as part of a skill token. '+' and '#' are significant
# (C++, C#) and must not be stripped as punctuation.
_SKILL_CHARS: Final = "a-z0-9+#"

# Accepted surface forms for skills whose common abbreviation differs from the
# canonical name. Kept deliberately small - every entry is an unambiguous
# synonym, because a loose alias reintroduces the false positives this module
# exists to eliminate.
SKILL_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "postgres": ("postgresql", "psql"),
    "postgresql": ("postgres", "psql"),
    "javascript": ("js", "ecmascript"),
    "typescript": ("ts",),
    "kubernetes": ("k8s",),
    "amazon web services": ("aws",),
    "google cloud platform": ("gcp",),
    "microsoft azure": ("azure",),
    "continuous integration": ("ci",),
    "machine learning": ("ml",),
    "natural language processing": ("nlp",),
    "large language model": ("llm", "large language models"),
    "restful api": ("rest api", "rest"),
}


@dataclass(slots=True)
class ATSResult:
    """Explainable outcome of the deterministic scoring pass."""

    keyword_score: float
    semantic_score: float
    experience_score: float
    completeness_score: float
    overall_score: float
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    detected_experience_years: float
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    recommendation: str = "LOW_MATCH"

    def score_breakdown(self) -> dict[str, float]:
        """Weighted contribution of each component, for the audit trail."""
        return {
            "keyword": round(self.keyword_score * WEIGHT_KEYWORD, 2),
            "semantic": round(self.semantic_score * WEIGHT_SEMANTIC, 2),
            "experience": round(self.experience_score * WEIGHT_EXPERIENCE, 2),
            "completeness": round(
                self.completeness_score * WEIGHT_COMPLETENESS, 2
            ),
        }


# -----------------------------------------------------------------------------
# Skill matching
# -----------------------------------------------------------------------------


def _skill_tokens(skill: str) -> list[str]:
    """Split a skill into tokens, preserving '+' and '#'."""
    return [t for t in re.split(r"[^\w+#]+", skill.casefold()) if t]


def _build_skill_pattern(skill: str) -> re.Pattern[str] | None:
    """Compile a boundary-anchored pattern for one skill surface form.

    Tokens are joined by a short flexible separator so 'Node.js', 'NodeJS' and
    'node js' all match, while the lookaround guards prevent a token from
    matching inside a longer word.
    """
    tokens = _skill_tokens(skill)
    if not tokens:
        return None

    body = r"[\s\-_/.]*".join(re.escape(token) for token in tokens)
    pattern = (
        rf"(?<![{_SKILL_CHARS}])({body})(?![{_SKILL_CHARS}])"
    )
    return re.compile(pattern, re.IGNORECASE)


def _surface_forms(skill: str) -> tuple[str, ...]:
    """The skill itself plus any unambiguous aliases."""
    canonical = "_".join(_skill_tokens(skill))
    return (skill, *SKILL_ALIASES.get(canonical, ()))


def _contains_skill(text: str, skill: str) -> bool:
    """True when 'text' evidences 'skill' at a token boundary.

    Replaces naïve substring containment: 'contains_skill(text, "R")' is
    false, and 'contains_skill("google cloud", "Go")' is false.
    """
    if not skill or not skill.strip() or not text:
        return False

    for form in _surface_forms(skill):
        pattern = _build_skill_pattern(form)
        if pattern is not None and pattern.search(text):
            return True
    return False


# -----------------------------------------------------------------------------
# Experience extraction
# -----------------------------------------------------------------------------

# "N+ years of professional experience" -- the candidate describing themselves.
EXPERIENCE_PHRASE_RE = re.compile(
    r"(?P<years>\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*"
    r"(?:years?|yrs?)"
    r"(?:\s+of)?\s+"
    r"(?:professional|hands-on|industry|work|total|as\s+a|relevant)?\s*"
    r"(?:experience|background)",
    re.IGNORECASE,
)

# Bare "N years", used only inside the experience section.
BARE_YEARS_RE = re.compile(r"(?P<years>\d+(?:\.\d+)?)\s*(?:years?|yrs?)", re.IGNORECASE)

# Phrasings where the years belong to an employer, a product or a course -
# not to the candidate.
CONTEXT_VENDOR_WORDS: Final = (
    r"(?:company|organization|firm|client|establishment|history|legacy|"
    r"client|production|system|tool|server|program|programming|with)"
)
CONTEXT_VENDOR_RE = re.compile(rf"\b{CONTEXT_VENDOR_WORDS}\b", re.IGNORECASE)

# Nobody has 40 years of professional experience; a match above this is a
# parse artefact (a year like "2015 years" from mangled PDF text).
MAX_PLAUSIBLE_YEARS: Final = 40.0


def _plausible(value: float) -> bool:
    return 0.0 < value <= MAX_PLAUSIBLE_YEARS


# How far back to look for a disqualifying subject, before clause clamping.
CONTEXT_WINDOW_CHARS: Final = 80

# Boundaries that end a clause. The lookback must not cross one, or an unrelated
# preceding sentence ("The organization has 40 years of history.") would
# disqualify a perfectly valid following claim.
CLAUSE_BOUNDARIES: Final = "\n.;!?"


def _preceding_clause(text: str, position: int) -> str:
    """Text immediately before 'position', clamped to the current clause."""
    window_start = max(0, position - CONTEXT_WINDOW_CHARS)
    window = text[window_start:position]

    boundary = max(window.rfind(char) for char in CLAUSE_BOUNDARIES)
    return window[boundary + 1:] if boundary != -1 else window


def _candidate_years_from_phrases(text: str) -> float:
    """'Years from explicit "N years of experience" phrasings."""
    best = 0.0
    for match in EXPERIENCE_PHRASE_RE.finditer(text):
        clause = _preceding_clause(text, match.start())
        if CONTEXT_VENDOR_RE.search(clause):
            # A vendor/company clause: 'subject' is an employer, not the candidate.
            continue

        value = float(match.group("years"))
        if _plausible(value):
            best = max(best, value)
    return best


def extract_experience_years(
    text: str, sections: dict[str, str] | None = None
) -> float:
    """Best estimate of the candidate's own years of experience.

    Prefers an explicit self-description. Falls back to bare "N years" mentions
    but only within the experience section, where the subject is unambiguous.
    """
    if not text:
        return 0.0

    explicit = _candidate_years_from_phrases(text)
    if explicit > 0.0:
        return explicit

    experience_section = (sections or {}).get("experience", "")
    if experience_section:
        candidates = [
            float(m.group("years")) for m in BARE_YEARS_RE.finditer(experience_section)
        ]
        plausible = [value for value in candidates if _plausible(value)]
        if plausible:
            return max(plausible)

    return 0.0


# -----------------------------------------------------------------------------
# Scoring
# -----------------------------------------------------------------------------


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _dedupe(skills: list[str]) -> list[str]:
    """Drop blanks and case-insensitive duplicates, preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        cleaned = skill.strip()
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def calculate_ats(
    resume_text: str,
    required_skills: list[str],
    preferred_skills: list[str],
    min_experience_years: int | None,
    section_count: int,
    *,
    semantic_score: float = 0.0,
    sections: dict[str, str] | None = None,
) -> ATSResult:
    """Score a resume against a job's requirements.

    `semantic_score` is supplied by the matcher node (local embedding
    similarity). When it is 0.0 -- embeddings disabled or unavailable -- the
    keyword score stands in for it, so the overall score stays on the same
    0-100 scale instead of being silently penalized by a missing component.
    """
    required = _dedupe(required_skills)
    preferred = _dedupe(preferred_skills)

    matched_required = [s for s in required if _contains_skill(resume_text, s)]
    missing_required = [s for s in required if s not in matched_required]
    matched_preferred = [s for s in preferred if _contains_skill(resume_text, s)]

    required_ratio = len(matched_required) / len(required) if required else 1.0
    preferred_ratio = len(matched_preferred) / len(preferred) if preferred else 1.0
    keyword_score = round(
        (
            required_ratio * REQUIRED_SKILL_WEIGHT * 100
            + preferred_ratio * PREFERRED_SKILL_WEIGHT * 100
        ),
        2,
    )

    effective_semantic = (
        round(_clamp(semantic_score), 2)
        if semantic_score > 0.0
        else keyword_score
    )

    detected_years = extract_experience_years(resume_text, sections)
    if not min_experience_years:
        experience_score = 100.0
    else:
        experience_score = round(
            _clamp((detected_years / min_experience_years) * 100), 2
        )

    completeness_score = round(
        _clamp((section_count / EXPECTED_SECTION_COUNT) * 100), 2
    )

    overall = round(
        keyword_score * WEIGHT_KEYWORD
        + effective_semantic * WEIGHT_SEMANTIC
        + experience_score * WEIGHT_EXPERIENCE
        + completeness_score * WEIGHT_COMPLETENESS,
        2,
    )

    strengths, concerns = _build_narrative(
        required=required,
        matched_required=matched_required,
        missing_required=missing_required,
        matched_preferred=matched_preferred,
        completeness_score=completeness_score,
        detected_years=detected_years,
        min_experience_years=min_experience_years,
    )

    return ATSResult(
        keyword_score=keyword_score,
        semantic_score=effective_semantic,
        experience_score=experience_score,
        completeness_score=completeness_score,
        overall_score=overall,
        matched_required=matched_required,
        missing_required=missing_required,
        matched_preferred=matched_preferred,
        detected_experience_years=detected_years,
        strengths=strengths,
        concerns=concerns,
        recommendation=recommend(overall, missing_required),
    )


def recommend(overall_score: float, missing_required: list[str]) -> str:
    """Map a score to a recommendation band.

    A candidate missing a *required* skill cannot be a strong match regardless
    of total score. Extracted to the sync and queued paths cannot drift apart,
    as they previously had.
    """
    if overall_score >= STRONG_MATCH_THRESHOLD and not missing_required:
        return "STRONG_MATCH"
    if overall_score >= REVIEW_THRESHOLD:
        return "REVIEW"
    return "LOW_MATCH"


def _build_narrative(
    *,
    required: list[str],
    matched_required: list[str],
    missing_required: list[str],
    matched_preferred: list[str],
    completeness_score: float,
    detected_years: float,
    min_experience_years: int | None,
) -> tuple[list[str], list[str]]:
    """Evidence-linked strengths and concerns.

    Each statement names the specific skills or sections behind it so a
    reviewer can trace the score back to the document.
    """
    strengths: list[str] = []
    concerns: list[str] = []

    if matched_required:
        strengths.append(
            f"Matched {len(matched_required)} of {len(required)} required skills: "
            f"{', '.join(matched_required)}."
        )

    if matched_preferred:
        strengths.append(
            f"Also evidences {len(matched_preferred)} preferred skills: "
            f"{', '.join(matched_preferred)}."
        )

    if completeness_score >= 80:
        strengths.append("Resume contains standard section headings and parses clearly.")

    if min_experience_years and detected_years >= min_experience_years:
        strengths.append(
            f"States around {detected_years} years of experience against a "
            f"{min_experience_years}-year requirement."
        )

    if missing_required:
        concerns.append(
            f"No evidence found for required skills: {', '.join(missing_required)}."
        )

    if min_experience_years and detected_years < min_experience_years:
        if detected_years == 0.0:
            concerns.append(
                f"Could not determine years of experience from the resume text; "
                f"the role requires {min_experience_years}+ years."
            )
        else:
            concerns.append(
                f"Detected about {detected_years} years against a "
                f"{min_experience_years}-year requirement."
            )

    if completeness_score < 80:
        concerns.append(
            "Several standard resume sections were not detected, which limits "
            "machine readability."
        )

    return strengths, concerns