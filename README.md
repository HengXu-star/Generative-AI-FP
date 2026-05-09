# LeaseLens: AI Rental Application Extractor

LeaseLens is a narrow GenAI workflow tool for leasing assistants and property managers. It takes a free-form rental application email or applicant note, extracts the key fields needed for review, and flags missing information for human follow-up.

## User and Workflow

The target user is a leasing assistant reviewing rental applications that arrive in inconsistent, unstructured text. In many small leasing teams, staff manually read applicant emails, copy fields into a spreadsheet or property management system, and then chase down anything missing.

LeaseLens helps with one specific workflow:

1. Read a rental application message.
2. Extract the core fields used in first-pass screening.
3. Flag missing information before the application moves forward.

This is intentionally a triage tool, not an automatic approval system.

## What I Built

The project includes:

- A `Streamlit` app for interactive extraction
- A rule-based baseline extractor using regex and keywords
- An LLM-based extractor using Groq's OpenAI-compatible Responses API with structured JSON output
- A small synthetic evaluation set with realistic rental application variations
- A simple evaluation script that compares baseline and LLM performance

The extracted fields are:

- applicant name
- email
- phone
- monthly income
- employer
- desired move-in date
- occupants
- pets
- guarantor
- missing fields
- human review notes

## Why GenAI Is Useful Here

Rental applications are often semi-structured instead of clean forms. Applicants might say:

- "I bring home around 4.8k a month"
- "My partner and I are hoping to move in late June"
- "My aunt can co-sign if needed"

A rule-based system works only when the wording follows predictable patterns. A GenAI model is useful because it can interpret varied natural language and return a consistent structured record.

## Baseline Comparison

The baseline is a simple regex and keyword extractor. It can reliably catch obvious patterns like email addresses, phone numbers, and some standard income phrases, but it struggles with:

- vague move-in language
- multiple applicants
- self-employment or freelance income
- indirect guarantor statements
- inconsistent wording about pets or occupancy

The LLM version uses structured outputs so the result is valid JSON with the same schema every time.

## Evaluation

I used `12` synthetic rental application cases with a mix of easy, medium, and hard examples. The cases include:

- standard applications with explicit fields
- informal emails
- missing information
- ambiguous dates
- multiple applicants
- students and freelancers
- guarantor edge cases

### What counted as good output

An output counted as good when it:

- extracted the correct field value
- returned `unknown` instead of guessing
- correctly listed missing fields
- produced notes for human review when the text was ambiguous or unusual

### How to run the evaluation

Baseline only:

```bash
python3 evaluate.py --mode baseline
```

Baseline + LLM:

```bash
export GROQ_API_KEY=your_key_here
python3 evaluate.py --mode both
```

The evaluation writes:

- [results/evaluation_summary.csv](/Users/mac/Downloads/RL/Generative AI FP/results/evaluation_summary.csv)
- [results/case_results.csv](/Users/mac/Downloads/RL/Generative AI FP/results/case_results.csv)

### Current checked result

I ran both the baseline and the LLM workflow on the 12-case synthetic evaluation set. The results were:

- Baseline field accuracy: `0.806`
- Baseline missing-field accuracy: `0.789`
- Baseline full-case completion accuracy: `0.333`
- Baseline triage success rate: `0.583`
- LLM field accuracy: `0.722`
- LLM missing-field accuracy: `0.944`
- LLM full-case completion accuracy: `0.000`
- LLM triage success rate: `0.333`

I added `triage_success_rate` as a more workflow-aligned metric. A case counts as a triage success when field accuracy is at least `0.70` and missing-field accuracy is at least `0.80`. This reflects the intended use case better than exact full-case match, because the tool is meant to support first-pass review rather than fully automate downstream decisions.

## What Worked

The rule-based baseline performed better on exact field extraction and on overall triage success in this small evaluation. That makes sense because many of the examples still contained obvious patterns that regex and keyword rules could capture reliably.

The LLM workflow was most useful for detecting incomplete applications. Its missing-field accuracy was significantly higher than the baseline, which suggests that GenAI adds value when the task is not only extraction, but also recognizing what information still needs human follow-up.

## What Failed and Where Humans Must Stay Involved

This tool has clear failure modes:

- annual income may be confused with monthly income
- multiple applicants can blur names, employers, and occupant counts
- vague timing like "late June" is not precise enough for downstream systems
- models may over-infer if prompting is weak
- exact-match evaluation can penalize outputs that are directionally useful but phrased differently

Because of that, a human should stay involved for:

- final screening decisions
- income verification
- guarantor verification
- conflict resolution when the text is incomplete or ambiguous

The right use case is first-pass extraction and missing-information triage, not autonomous approval.

## How to Run the App

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your API key:

```bash
export GROQ_API_KEY=your_key_here
```

Run the app:

```bash
streamlit run app.py
```

## Repository Structure

```text
.
├── app.py
├── extractor_baseline.py
├── extractor_llm.py
├── evaluate.py
├── schema.py
├── data/
│   ├── examples.json
│   └── eval_cases.json
├── results/
│   ├── case_results.csv
│   └── evaluation_summary.csv
└── requirements.txt
```
