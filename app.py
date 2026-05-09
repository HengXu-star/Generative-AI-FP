"""Streamlit app for the LeaseLens rental application extractor."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from extractor_baseline import extract_baseline, summarize_known_fields
from extractor_llm import LLMExtractorError, extract_with_llm


ROOT = Path(__file__).resolve().parent
EXAMPLES_PATH = ROOT / "data" / "examples.json"


def load_examples() -> list[dict[str, str]]:
    return json.loads(EXAMPLES_PATH.read_text())


st.set_page_config(page_title="LeaseLens", page_icon="🏠", layout="wide")
st.title("LeaseLens")
st.caption("Extract rental application details from free-form applicant text.")

examples = load_examples()
labels = ["Custom input"] + [f"{item['title']}" for item in examples]
selected_label = st.selectbox("Example", labels)

default_text = ""
if selected_label != "Custom input":
    for example in examples:
        if example["title"] == selected_label:
            default_text = example["input"]
            break

input_text = st.text_area(
    "Rental application text",
    value=default_text,
    height=260,
    placeholder="Paste an applicant email or application note here.",
)

model = st.text_input("Groq model", value="llama-3.1-8b-instant")
run_button = st.button("Extract fields", type="primary")


def render_result(title: str, result: dict[str, object], status: str) -> None:
    st.subheader(title)
    st.metric("Known fields", summarize_known_fields(result), 9)
    st.caption(status)
    st.json(result)


if run_button:
    if not input_text.strip():
        st.warning("Please paste rental application text before running extraction.")
    else:
        col1, col2 = st.columns(2)

        baseline = extract_baseline(input_text)
        with col1:
            render_result("Baseline Extractor", baseline, "Regex + keyword baseline")

        with col2:
            try:
                llm_result = extract_with_llm(input_text, model=model)
                render_result("LLM Extractor", llm_result, f"Groq model: {model}")
            except LLMExtractorError as exc:
                st.subheader("LLM Extractor")
                st.error(str(exc))

        st.markdown("### Suggested human review")
        st.write(
            "Use this tool for first-pass triage only. A leasing assistant should still "
            "verify income, guarantor details, and any ambiguous move-in timing in the original text."
        )
