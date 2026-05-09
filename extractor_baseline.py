"""Rule-based baseline extractor for rental application text."""

from __future__ import annotations

import re
from typing import Dict

from schema import FIELDS, empty_result, normalize_missing_fields


EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b", re.IGNORECASE)
PHONE_RE = re.compile(
    r"(?:\+?1[\s.-]*)?(?:\(?\d{3}\)?[\s.-]*)\d{3}[\s.-]*\d{4}"
)
INCOME_RE = re.compile(
    r"(\$ ?\d[\d,]*(?:\.\d+)?(?:k|K)?(?:\s*(?:per month|/month|monthly|a month))?|"
    r"\b\d+(?:\.\d+)?k\s+annually\b)",
    re.IGNORECASE,
)
MOVE_IN_RE = re.compile(
    r"\b(?:move in|moving|start(?:ing)? lease|start the lease|lease start|hoping to move in|"
    r"would move|looking for a)"
    r"[^.:\n]{0,40}\b(?:on\s+)?"
    r"([A-Z][a-z]+(?:\s+\d{1,2})?(?:,\s*\d{4})?|late\s+[A-Z][a-z]+|early\s+[A-Z][a-z]+|"
    r"mid[- ]?[A-Z][a-z]+|end of\s+[A-Z][a-z]+|September|October|November)\b",
    re.IGNORECASE,
)
EMPLOYER_RE = re.compile(
    r"\b(?:work(?:ing)? at|employed by|currently at|accepted a new role with|starting at)\s+"
    r"([A-Z][A-Za-z0-9'&,. -]+?)(?=\.|,| and |\.|$)",
    re.IGNORECASE,
)
NAME_RE = re.compile(
    r"\b(?:my name is|i am|i'm|this is|we are)\s+"
    r"([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z][a-z]+){0,4})\b",
    re.IGNORECASE,
)
OCCUPANT_RE = re.compile(
    r"\b(?:just me|only me|myself|only tenant|would be the only tenant)\b|"
    r"\b(\d)\s+(?:people|occupants|tenants|adults)\b|"
    r"\b(my partner and i|my roommate and i|my wife and i|my husband and i|we are [A-Z][a-z]+ and [A-Z][a-z]+)\b",
    re.IGNORECASE,
)
PET_RE = re.compile(
    r"\b(no pets|one small dog|one dog|one cat|two cats|two dogs|small dog|small cat|dog|cat|pet|pets)\b",
    re.IGNORECASE,
)
GUARANTOR_RE = re.compile(
    r"([^.:\n]{0,35}\b(?:guarantor|co-signer|cosigner)\b[^.:\n]{0,35})",
    re.IGNORECASE,
)


def _clean_match(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" .,:;\n"))


def extract_baseline(text: str) -> Dict[str, object]:
    result = empty_result()
    lowered = text.lower()

    email_match = EMAIL_RE.search(text)
    if email_match:
        result["email"] = email_match.group(0)

    phone_match = PHONE_RE.search(text)
    if phone_match:
        result["phone"] = _clean_match(phone_match.group(0))

    name_match = NAME_RE.search(text)
    if name_match:
        result["applicant_name"] = _clean_match(name_match.group(1))

    income_match = INCOME_RE.search(text)
    if income_match:
        result["monthly_income"] = _clean_match(income_match.group(1))

    move_in_match = MOVE_IN_RE.search(text)
    if move_in_match:
        result["desired_move_in_date"] = _clean_match(move_in_match.group(1))

    employer_match = EMPLOYER_RE.search(text)
    if employer_match:
        result["employer"] = _clean_match(employer_match.group(1))

    occupant_match = OCCUPANT_RE.search(text)
    if occupant_match:
        if occupant_match.group(0).lower() in {"just me", "only me", "myself", "only tenant", "would be the only tenant"}:
            result["occupants"] = "1"
        elif occupant_match.group(1):
            result["occupants"] = occupant_match.group(1)
        else:
            result["occupants"] = "2"
    elif re.search(r"\bit(?: would|'d)? just be me\b|\bit'?s only me\b", lowered):
        result["occupants"] = "1"

    pet_match = PET_RE.search(text)
    if pet_match:
        pet_value = pet_match.group(1).lower()
        if pet_value == "pet":
            pet_value = "has pet"
        result["pets"] = pet_value

    guarantor_match = GUARANTOR_RE.search(text)
    if guarantor_match:
        result["guarantor"] = _clean_match(guarantor_match.group(1))
    elif "no guarantor" in lowered or "no co-signer" in lowered:
        result["guarantor"] = "none"
    elif "self-employed" in lowered or "freelance" in lowered:
        result["employer"] = "self-employed" if "self-employed" in lowered else "freelance"

    notes = []
    if result["applicant_name"] == "unknown" and email_match:
        notes.append("Could not confidently find the applicant's name.")
    if result["monthly_income"] != "unknown" and "year" in result["monthly_income"].lower():
        notes.append("Income may be annual rather than monthly.")
    if "partner and i" in lowered or "roommate and i" in lowered:
        notes.append("Multiple applicants may require manual review.")
    result["notes_for_human_review"] = " ".join(notes)
    return normalize_missing_fields(result)


def summarize_known_fields(result: Dict[str, object]) -> int:
    """Count non-missing business fields for quick display."""
    return sum(1 for field in FIELDS if result.get(field, "unknown") != "unknown")
