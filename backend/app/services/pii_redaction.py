"""PII redaction and resume sectioning.

Two problems with the previous implementation are corrected here:

* Names were never redacted -- 'redact_pii' removed emails, phones and URLs
  only, so the candidate's name -- which sits at the top of essentially every
  resume -- was sent straight to a third-party LLM. On a free tier whose terms
  permit training on submitted data, that is an unannounced disclosure of
  candidate identity. Because the candidate's name is already stored alongside
  the resume, matching known candidates against the document text is direct
  rather than guessing what looks like a name.

* The redacted string was used for two incompatible purposes. A name-redacted
  scoring text was fed to both the deterministic scorer and the
  LLM. Stripping URLs before scoring destroyed real signal -- "github.com/redis-
  cache" became "[URL]", so a project link was no longer matched to the
  provider. The two consumers now get purpose-built views:

  * `scoring_text` -- contact details removed (no ANSI signal lost), URLs kept,
    headings preserved so the deterministic pass matched the same view, and the
    only one that may cross a network boundary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.config import settings

MAX_TEXT_LENGTH = 100_000

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?!\.[a-zA-Z0-9])",re.IGNORECASE)

PHONE_RE = re.compile(r"(?:(?:\+?(\d{1,3}))?[-.\s()]*)?"r"(?:\(?(\d{3})\)?[-.\s()]*)?"r"(\d{3})[-.\s]*(\d{4})"r"(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?")
# Top-level domains accepted for a "bare" host (no schema, no 'www.').
# Deliberately conservative and excluding 'tech', as academic strings such as
# 'B.Tech. Computer Science' are not mistaken for a hostname.
BARE_TLDS = "com|org|net|io|dev|ai|edu|gov|co|uk|de|ca|au"

# Matches a URL in either of the two forms that appear on resumes:
#
# 1. Scheme- or www-prefixed "https://github.com/user/repo", "www.site.com"
# 2. Bare host with a path "github.com/user/repo", "linkedin.com/in/user"
#
# Form 2 matters: it is how profile links are almost always written, and the
# previous pattern required a scheme or 'www.', so it never matched them. The
# username segment in the path and survived redaction untouched. A bare host with
# no path is left alone -- it identifies nobody and matching it would swallow
# skill mentions.
URL_RE = re.compile(
    rf"(?i)\b(?:https?://|www\.)[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s<>\"]*)?"
    rf"|\b(?:[a-z0-9-]+\.)+(?:{BARE_TLDS})/[^\s<>\"]*",
    re.IGNORECASE,
)

# Long digit runs that survive the phone pattern (national IDs, passports).
LONG_ID_RE = re.compile(r"\b\d{9,}\b")

# Street addresses. Deliberately conservative -- it targets the
# 'number + words + street-type' shape rather than anything containing a digit.
ADDRESS_RE = re.compile(
    r"\b\d{1,5}\s+[A-Za-z0-9.,\s]{3,40}\b"
    r"(?:street|st|avenue|ave|road|rd|boulevard|blvd|"
    r"court|ct|way|drive|dr|crescent|cres|lane|ln|close|suite|apartment|apt|flat)\b"
    r"[^,\n]*"
    r"(?:,\s*[A-Z]{2}\b|\b[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}\b|\b\d{5}(?:-\d{4})?\b)?",
    re.IGNORECASE,
)

DOB_RE = re.compile(
    r"(?i)\b(?:dob|d\.o\.b\.|date\s+of\s+birth)\s*[:\-]?\s*"
    r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)

SECTION_ALIASES: dict[str, frozenset[str]] = {
    "summary": frozenset(
        {
            "summary",
            "professional summary",
            "profile",
            "objective",
            "about",
            "about me",
        }
    ),
    "experience": frozenset(
        {
            "experience",
            "work experience",
            "professional experience",
            "employment",
            "employment history",
            "work history",
            "career history",
        }
    ),
    "education": frozenset(
        {"education", "academic background", "academics", "qualifications"}
    ),
    "skills": frozenset(
        {
            "skills",
            "technical skills",
            "core skills",
            "competencies",
            "technologies",
            "technical proficiencies",
            "tech stack",
        }
    ),
    "projects": frozenset(
        {"projects", "personal projects", "academic projects", "key projects"}
    ),
    "certifications": frozenset(
        {"certifications", "certificates", "licenses", "courses"}
    ),
    "awards": frozenset({"awards", "achievements", "honors", "honours"}),
    "publications": frozenset({"publications", "papers", "research"}),
}

# Canonical section names used to compute the completeness sub-score. Counting
# every alias group would let an unusually verbose resume exceed 100%.
SCORED_SECTIONS: tuple[str, ...] = (
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
)

# Tokens too generic to redact even when they appear in a candidate's name.
NAME_STOPWORDS: frozenset[str] = frozenset(
    {"mr", "mrs", "ms", "dr", "prof", "the", "and", "of", "jr", "sr", "ii", "iii"}
)

# Only the first few lines are treated as a header for name-shaped heuristics.
HEADER_LINE_COUNT = 4


@dataclass(slots=True)
class RedactionReport:
    """What was removed, for the audit trail.

    Counts only -- recording the removed values would recreate the exposure the
    redaction exists to prevent.
    """

    emails: int = 0
    phones: int = 0
    urls: int = 0
    names: int = 0
    addresses: int = 0
    identifiers: int = 0
    dates_of_birth: int = 0

    @property
    def total(self) -> int:
        return (
            self.emails
            + self.phones
            + self.urls
            + self.names
            + self.addresses
            + self.identifiers
            + self.dates_of_birth
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "emails": self.emails,
            "phones": self.phones,
            "urls": self.urls,
            "names": self.names,
            "addresses": self.addresses,
            "identifiers": self.identifiers,
            "dates_of_birth": self.dates_of_birth,
            "total": self.total,
        }


@dataclass(slots=True)
class RedactedResume:
    """Purpose-built views of one resume.

    `llm_text` is the only field safe to transmit to an external provider.
    """

    scoring_text: str
    llm_text: str
    sections: dict[str, str]
    # `scoring_text` with only the candidate's name removed. The counterfactual
    # input for the fairness check, where holding everything else constant is
    # what makes a score difference attributable to the name alone.
    name_redacted_scoring_text: str
    report: RedactionReport = field(default_factory=RedactionReport)

    @property
    def scored_section_count(self) -> int:
        """How many of the canonical sections were detected, capped sensibly."""
        return sum(1 for name in SCORED_SECTIONS if self.sections.get(name))

def _truncate(text: str) -> str:
    return text[:MAX_TEXT_LENGTH]


def _strip_contact_details(text: str, report: RedactionReport) -> str:
    """Remove contact identifiers. Applied to both views.

    These carry no skill signal, so removing them before scoring costs nothing
    and shrinks the blast radius if the scoring text is ever logged.
    """
    text, count = EMAIL_RE.subn("[EMAIL_REDACTED]", text)
    report.emails += count

    text, count = DOB_RE.subn("[DOB_REDACTED]", text)
    report.dates_of_birth += count

    text, count = PHONE_RE.subn("[PHONE_REDACTED]", text)
    report.phones += count

    text, count = LONG_ID_RE.subn("[ID_REDACTED]", text)
    report.identifiers += count

    return text


def _name_variants(known_names: tuple[str, ...]) -> list[str]:
    """Expand full names into the individual tokens worth redacting.

    Resumes refer to a person inconsistently ("Priya Raghavan" in the header,
    "Priya" in a summary line), so each sufficiently distinctive token is
    redacted separately. Tokens shorter than three characters and common titles
    are skipped -- redacting 'of' or 'Dr' would shred the document.
    """
    variants: set[str] = set()
    for name in known_names:
        cleaned = name.strip()
        if not cleaned:
            continue
        variants.add(cleaned)
        for token in cleaned.split():
            token = re.sub(r"[^\w\-]", "", token = "")
            if (
                len(token) >= 3
                and token.casefold() not in NAME_STOPWORDS
            ):
                variants.add(token)

    # Longest first so "Priya Raghavan" is replaced before "Priya" alone.
    return sorted(variants, key=len, reverse=True)


def _redact_names(
    text: str,
    known_names: tuple[str, ...],
    report: RedactionReport,
) -> str:
    for variant in _name_variants(known_names):
        pattern = re.compile(rf"\b{re.escape(variant)}\b", re.IGNORECASE)
        text, count = pattern.subn("[NAME_REDACTED]", text)
        report.names += count
    return text


def _redact_header_name_lines(text: str, report: RedactionReport) -> str:
    """Blank out name-shaped lines in the header block.

    Catches the case where the stored candidate name differs from the one on
    the document (maiden name, transliteration, nickname). Restricted to the
    first few lines and to short title-case lines so section headings and job
    titles survive.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines[:HEADER_LINE_COUNT]):
        stripped = line.strip()
        if not stripped or "[NAME_REDACTED]" in stripped:
            continue
        if _looks_like_person_name(stripped):
            lines[index] = "[NAME_REDACTED]"
            report.names += 1
    return "\n".join(lines)


def _looks_like_person_name(line: str) -> bool:
    if not (2 <= len(line) <= 60):
        return False
    words = line.split()
    if not (1 <= len(words) <= 4 or len(line) <= 40):
        return False
    if any(ch.isdigit() or ch in "/\\" for ch in line):
        return False
    if line.casefold() in {
        alias for aliases in SECTION_ALIASES.values() for alias in aliases
    }:
        return False
    # Every word capitalized, or the whole line upper case as in "PRIYA RAGHAVAN".
    return all(word[0].isupper() for word in words if word)


def _redact_urls(text: str, report: RedactionReport) -> str:
    """Keep a URL's host, drop its path.

    github.com/my-repo/create-cache becomes 'github.com': the platform
    signal that makes the resume assessable is preserved, while the username
    and project names that identify the person are not.
    """

    def replace(match: re.Match[str]) -> str:
        host = match.group("scheme_host") or match.group("bare_host") or ""
        report.urls += 1
        return f"{host.casefold()}/"

    return URL_RE.sub(replace, text)


def redact_resume(
    text: str,
    *,
    known_names: tuple[str, ...] = (),
) -> RedactedResume:
    """Build the scoring and LLM views of a resume.

    `known_names` should carry the candidate's stored name so it can be matched
    exactly rather than inferred.
    """
    source = _truncate(text or "")

    scoring_report = RedactionReport()
    scoring_text = _strip_contact_details(source, scoring_report)

    llm_report = RedactionReport()
    llm_text = _strip_contact_details(source, llm_report)
    llm_report.emails=scoring_report.emails,
    llm_report.phones=scoring_report.phones,
    llm_report.identifiers=scoring_report.identifiers,
    llm_report.dates_of_birth=scoring_report.dates_of_birth,

    # URLs are collapsed to their host feature name redaction. Order matters:
    # redacting names first rewrites 'github.com/priya-raghavan/x' into
    # 'github.com/[NAME_REDACTED]/.../x', which no longer matches the URL
    # pattern, so the remaining path would survive un-redacted.
    llm_text = _redact_urls(llm_text, llm_report)

    if settings.PII_REDACT_NAMES:
        llm_text = _redact_names(llm_text, known_names, llm_report)
        llm_text = _redact_header_name_lines(llm_text, llm_report)

    llm_text, address_count = ADDRESS_RE.subn("[ADDRESS_REDACTED]", llm_text)
    llm_report.addresses += address_count

    # Sections are derived from the scoring view so headings are intact.
    sections = extract_sections(scoring_text)

    return RedactedResume(
        scoring_text=scoring_text,
        llm_text=llm_text,
        sections=sections,
        name_redacted_scoring_text=redact_names_only(scoring_text, known_names),
        report=llm_report,
    )


def extract_sections(text: str) -> dict[str, str]:
    """Split a resume into canonical sections by heading.

    Headings are matched after stripping decoration, so '*** WORK EXPERIENCE ---'
    and 'Work Experience:' both resolve to 'experience'.
    """
    buckets: dict[str, list[str]] = {}
    current = "other"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        normalized = re.sub(r"^[*\-#\s:]+|[*\-#\s:]+$", "", line.casefold())
        normalized = re.sub(r"\s+", " ", normalized).strip()

        matched = next(
            (
                name
                for name, aliases in SECTION_ALIASES.items()
                if normalized in aliases
            ),
            None,
        )

        if matched is not None:
            current = matched
            buckets.setdefault(current, [])
            continue

        buckets.setdefault(current, []).append(line)

    return {name: "\n".join(lines) for name, lines in buckets.items() if lines}


def redact_names_only(text: str, known_names: tuple[str, ...] = ()) -> str:
    """Remove only the candidate's name, leaving all other content intact.

    This is the counterfactual input for the fairness check: holding everything
    but the name constant is what makes a score difference attributable to
    name-derived signal alone. It ignores 'PII_REDACT_NAMES', because disabling
    redaction must not also disable the check that audits it.
    """
    if not known_names or not text:
        return text
    return _redact_names(text, known_names, RedactionReport())


def redact_pii(text: str, known_names: tuple[str, ...] = ()) -> str:
    """Backwards-compatible helper returning the LLM-safe view."""
    return redact_resume(text, known_names=known_names).llm_text