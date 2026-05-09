# LeaseLens Presentation Outline

## Slide 1: Context, User, and Problem

- User: leasing assistant or property manager
- Workflow: review rental application messages and enter applicant details into a system
- Problem: applications arrive in free-form text, so manual extraction is slow and inconsistent
- Why it matters: slow review delays follow-up and missing fields create back-and-forth with applicants

## Slide 2: Solution and Design

- Built a small Streamlit app called LeaseLens
- Input: rental application email or note
- Output: structured applicant fields plus missing-field flags
- Design choice: compare a rule-based baseline with an OpenAI structured-output workflow
- Keep the scope narrow: this is a first-pass extraction tool, not an automated approval system

## Slide 3: Evaluation and Results

- Evaluated on 12 synthetic application cases
- Baseline: regex and keyword extraction
- LLM workflow: structured JSON extraction
- Baseline field accuracy measured locally: `0.806`
- Baseline missing-field accuracy measured locally: `0.789`
- Baseline full-case completion measured locally: `0.333`
- Human must still review ambiguous income, move-in dates, and guarantor details

## Slide 4: Artifact Snapshot

Use this actual prototype image:

![LeaseLens Prototype](/Users/mac/Downloads/RL/Generative AI FP/assets/prototype_snapshot.png)

Talking points for this slide:

- Left side shows a realistic applicant email pasted into the app
- Right side shows the structured extraction record the tool returns
- The tool highlights what is still missing, such as guarantor information
- This is the main business value: turn messy text into a review-ready record faster

## Optional closing sentence

"LeaseLens works best as a triage assistant: it speeds up the boring extraction step, but a human should still verify important details before any leasing decision."
