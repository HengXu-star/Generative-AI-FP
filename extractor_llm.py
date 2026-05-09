"""LLM-powered extractor using Groq's OpenAI-compatible Chat Completions API."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Dict

from schema import normalize_missing_fields


SYSTEM_PROMPT = """You extract fields from rental application text.

Return one JSON object only with exactly these keys:
applicant_name, email, phone, monthly_income, employer, desired_move_in_date,
occupants, pets, guarantor, missing_fields, notes_for_human_review

Rules:
- Every value except missing_fields must be a string.
- missing_fields must be an array of zero or more names from:
  applicant_name, email, phone, monthly_income, employer,
  desired_move_in_date, occupants, pets, guarantor
- Use "unknown" for any field that is missing, ambiguous, or unsupported.
- Do not guess.
- Keep values extremely short.
- Keep notes_for_human_review empty unless something truly needs review.
- Return valid JSON only. No markdown, no explanation.
"""


class LLMExtractorError(RuntimeError):
    """Raised when LLM extraction cannot be completed."""


def _extract_json_object(text: str) -> Dict[str, object]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMExtractorError(f"Model did not return a JSON object: {text}")
    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise LLMExtractorError(f"Model returned invalid JSON: {snippet}") from exc


def extract_with_llm(
    text: str,
    *,
    model: str = "llama-3.1-8b-instant",
    api_key: str | None = None,
) -> Dict[str, object]:
    api_key = api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMExtractorError("GROQ_API_KEY is not set.")

    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }

    def send_request(attempt: int = 0) -> Dict[str, object]:
        request = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "LeaseLens/1.0 (+https://github.com/HengXu-star/Generative-AI-FP)",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code == 429 and attempt < 4:
                retry_seconds = 3.0
                match = re.search(r"try again in ([0-9.]+)s", body, re.IGNORECASE)
                if match:
                    retry_seconds = max(float(match.group(1)) + 0.5, retry_seconds)
                time.sleep(retry_seconds)
                return send_request(attempt + 1)
            raise LLMExtractorError(f"Groq API error: {exc.code} {body}") from exc
        except urllib.error.URLError as exc:
            raise LLMExtractorError(f"Network error calling Groq API: {exc}") from exc

        return json.loads(raw)

    parsed = send_request()
    if parsed.get("error"):
        raise LLMExtractorError(str(parsed["error"]))

    try:
        content = parsed["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMExtractorError(f"Unexpected Groq response: {parsed}") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMExtractorError(f"Empty model output: {parsed}")

    result = _extract_json_object(content)
    return normalize_missing_fields(result)
