"""Shared schema and helpers for the LeaseLens project."""

from __future__ import annotations

from typing import Dict, List


FIELDS: List[str] = [
    "applicant_name",
    "email",
    "phone",
    "monthly_income",
    "employer",
    "desired_move_in_date",
    "occupants",
    "pets",
    "guarantor",
]


def empty_result() -> Dict[str, object]:
    """Return a blank extraction record."""
    result: Dict[str, object] = {field: "unknown" for field in FIELDS}
    result["missing_fields"] = []
    result["notes_for_human_review"] = ""
    return result


def normalize_missing_fields(result: Dict[str, object]) -> Dict[str, object]:
    """Ensure missing fields are aligned with unknown values."""
    missing = set()
    for field in FIELDS:
        value = str(result.get(field, "unknown")).strip()
        if not value:
            value = "unknown"
        result[field] = value
        if value.lower() == "unknown":
            missing.add(field)

    declared_missing = result.get("missing_fields", [])
    if isinstance(declared_missing, list):
        missing.update(str(item) for item in declared_missing if str(item) in FIELDS)

    result["missing_fields"] = sorted(missing)
    result["notes_for_human_review"] = str(result.get("notes_for_human_review", "")).strip()
    return result


JSON_SCHEMA = {
    "name": "rental_application_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "applicant_name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "monthly_income": {"type": "string"},
            "employer": {"type": "string"},
            "desired_move_in_date": {"type": "string"},
            "occupants": {"type": "string"},
            "pets": {"type": "string"},
            "guarantor": {"type": "string"},
            "missing_fields": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": FIELDS,
                },
            },
            "notes_for_human_review": {"type": "string"},
        },
        "required": FIELDS + ["missing_fields", "notes_for_human_review"],
    },
}
