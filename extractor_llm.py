"""LLM-powered extractor using OpenAI's Responses API."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Dict

from schema import JSON_SCHEMA, normalize_missing_fields


SYSTEM_PROMPT = """You extract fields from rental application text.

Return JSON that matches the provided schema exactly.
Rules:
- Use "unknown" for any field that is missing, ambiguous, or not explicitly supported by the text.
- Do not guess or infer unstated facts.
- Keep values short and close to the source wording.
- Use notes_for_human_review to flag ambiguity, multiple applicants, conflicting details, or unusual edge cases.
"""


class LLMExtractorError(RuntimeError):
    """Raised when LLM extraction cannot be completed."""


def _extract_output_text(payload: Dict[str, object]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                return content["text"]

    raise LLMExtractorError("OpenAI response did not contain text output.")


def extract_with_llm(
    text: str,
    *,
    model: str = "gpt-4.1-mini",
    api_key: str | None = None,
) -> Dict[str, object]:
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMExtractorError("OPENAI_API_KEY is not set.")

    payload = {
        "model": model,
        "instructions": SYSTEM_PROMPT,
        "input": text,
        "max_output_tokens": 600,
        "text": {
            "format": {
                "type": "json_schema",
                "name": JSON_SCHEMA["name"],
                "schema": JSON_SCHEMA["schema"],
                "strict": JSON_SCHEMA["strict"],
            }
        },
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise LLMExtractorError(f"OpenAI API error: {exc.code} {body}") from exc
    except urllib.error.URLError as exc:
        raise LLMExtractorError(f"Network error calling OpenAI API: {exc}") from exc

    parsed = json.loads(raw)
    if parsed.get("status") == "incomplete":
        raise LLMExtractorError(f"Incomplete response: {parsed.get('incomplete_details')}")
    if parsed.get("error"):
        raise LLMExtractorError(str(parsed["error"]))

    content = _extract_output_text(parsed)
    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMExtractorError(f"Model returned invalid JSON: {content}") from exc

    return normalize_missing_fields(result)
