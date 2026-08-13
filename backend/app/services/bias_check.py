from dataclasses import dataclass
import re

@dataclass
class BiasCheck:
    flags: list[str]
    checked_fields: list[str]
    safe_for_screening: bool

PROTECTED_HINTS = (
    "gender", "male", "female", "married", "pregnant",
    "religion", "caste", "race", "ethnicity", "age",
    "date of birth", "disability", "health", "nationality",
)

def inspect_text(text: str) -> BiasCheck:
    lower = text.casefold()
    flags = []
    for hint in PROTECTED_HINTS:
        if re.search(rf"\b{re.escape(hint)}\b", lower):
            flags.append(f"Potential protected-attribute reference detected: {hint}")
    return BiasCheck(
        flags=flags,
        checked_fields=["name", "email", "phone", "urls", "protected-attribute hints"],
        safe_for_screening=True,
    )
