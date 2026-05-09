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
- An LLM-based extractor using the OpenAI Responses API with structured JSON output
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
export OPENAI_API_KEY=your_key_here
python3 evaluate.py --mode both
```

The evaluation writes:

- [results/evaluation_summary.csv](/Users/mac/Downloads/RL/Generative AI FP/results/evaluation_summary.csv)
- [results/case_results.csv](/Users/mac/Downloads/RL/Generative AI FP/results/case_results.csv)

### Current checked result

I was able to run the baseline locally in this repository. On the 12-case synthetic set, the baseline produced:

- field accuracy: `0.806`
- missing-field accuracy: `0.789`
- full-case completion accuracy: `0.333`

I could not run the OpenAI comparison inside this environment because `OPENAI_API_KEY` was not configured. The LLM evaluation path is implemented and can be run immediately once a key is added.

## What Worked

The baseline works reasonably well on clean, explicit cases. The overall workflow is still useful because it exposes how much rental screening depends on reading messy human language.

The LLM design is expected to do better than the baseline on:

- paraphrased income descriptions
- natural move-in date phrasing
- soft or indirect guarantor mentions
- multi-applicant summaries

## What Failed and Where Humans Must Stay Involved

This tool has clear failure modes:

- annual income may be confused with monthly income
- multiple applicants can blur names, employers, and occupant counts
- vague timing like "late June" is not precise enough for downstream systems
- models may over-infer if prompting is weak

Because of that, a human should stay involved for:

- final screening decisions
- income verification
- guarantor verification
- conflict resolution when the text is incomplete or ambiguous

The right use case is first-pass extraction and triage, not autonomous approval.

## How to Run the App

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your API key:

```bash
export OPENAI_API_KEY=your_key_here
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
├── requirements.txt
└── slides.md
```
