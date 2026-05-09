"""Evaluation script for comparing the baseline with the LLM extractor."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List

from extractor_baseline import extract_baseline
from extractor_llm import LLMExtractorError, extract_with_llm
from schema import FIELDS


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "eval_cases.json"
RESULTS_PATH = ROOT / "results" / "evaluation_summary.csv"
DETAILS_PATH = ROOT / "results" / "case_results.csv"


def normalize_value(value: object) -> str:
    return " ".join(str(value).strip().lower().split())


def score_case(prediction: Dict[str, object], truth: Dict[str, object]) -> Dict[str, float]:
    field_correct = 0
    for field in FIELDS:
        if normalize_value(prediction.get(field, "unknown")) == normalize_value(truth.get(field, "unknown")):
            field_correct += 1

    truth_missing = sorted(str(item) for item in truth.get("missing_fields", []))
    pred_missing = sorted(str(item) for item in prediction.get("missing_fields", []))
    truth_missing_set = set(truth_missing)
    pred_missing_set = set(pred_missing)
    union_size = len(truth_missing_set | pred_missing_set)
    missing_match = (
        len(truth_missing_set & pred_missing_set) / union_size if union_size else 1.0
    )

    case_complete = 1.0 if field_correct == len(FIELDS) and missing_match == 1.0 else 0.0
    triage_success = (
        1.0
        if (field_correct / len(FIELDS)) >= 0.70 and missing_match >= 0.80
        else 0.0
    )
    return {
        "field_accuracy": field_correct / len(FIELDS),
        "missing_field_accuracy": missing_match,
        "case_completion_accuracy": case_complete,
        "triage_success": triage_success,
    }


def aggregate_scores(rows: Iterable[Dict[str, object]]) -> Dict[str, float]:
    rows = list(rows)
    if not rows:
        return {
            "cases": 0,
            "field_accuracy": 0.0,
            "missing_field_accuracy": 0.0,
            "case_completion_accuracy": 0.0,
            "triage_success_rate": 0.0,
        }

    return {
        "cases": len(rows),
        "field_accuracy": sum(row["field_accuracy"] for row in rows) / len(rows),
        "missing_field_accuracy": sum(row["missing_field_accuracy"] for row in rows) / len(rows),
        "case_completion_accuracy": sum(row["case_completion_accuracy"] for row in rows) / len(rows),
        "triage_success_rate": sum(row["triage_success"] for row in rows) / len(rows),
    }


def load_cases() -> List[Dict[str, object]]:
    return json.loads(DATA_PATH.read_text())


def evaluate_extractor(cases: List[Dict[str, object]], mode: str, model: str) -> List[Dict[str, object]]:
    rows = []
    for case in cases:
        if mode == "baseline":
            prediction = extract_baseline(case["input"])
        else:
            prediction = extract_with_llm(case["input"], model=model)

        scores = score_case(prediction, case["expected"])
        rows.append(
            {
                "mode": mode,
                "case_id": case["id"],
                "difficulty": case["difficulty"],
                **scores,
            }
        )
    return rows


def write_case_results(rows: List[Dict[str, object]]) -> None:
    DETAILS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DETAILS_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "mode",
                "case_id",
                "difficulty",
                "field_accuracy",
                "missing_field_accuracy",
                "case_completion_accuracy",
                "triage_success",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_summary(rows: List[Dict[str, object]]) -> None:
    modes = sorted(set(row["mode"] for row in rows))
    summary_rows = []
    for mode in modes:
        summary = aggregate_scores(row for row in rows if row["mode"] == mode)
        summary_rows.append({"mode": mode, **summary})

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "mode",
                "cases",
                "field_accuracy",
                "missing_field_accuracy",
                "case_completion_accuracy",
                "triage_success_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate LeaseLens extractors.")
    parser.add_argument(
        "--mode",
        choices=["baseline", "llm", "both"],
        default="both",
        help="Which extractor(s) to evaluate.",
    )
    parser.add_argument(
        "--model",
        default="llama-3.1-8b-instant",
        help="Groq model for the LLM evaluation.",
    )
    args = parser.parse_args()

    cases = load_cases()
    all_rows: List[Dict[str, object]] = []

    if args.mode in {"baseline", "both"}:
        all_rows.extend(evaluate_extractor(cases, "baseline", args.model))

    if args.mode in {"llm", "both"}:
        try:
            all_rows.extend(evaluate_extractor(cases, "llm", args.model))
        except LLMExtractorError as exc:
            print(f"Skipping LLM evaluation: {exc}")

    write_case_results(all_rows)
    write_summary(all_rows)

    for mode in sorted(set(row["mode"] for row in all_rows)):
        summary = aggregate_scores(row for row in all_rows if row["mode"] == mode)
        print(
            f"{mode}: "
            f"cases={summary['cases']}, "
            f"field_accuracy={summary['field_accuracy']:.3f}, "
            f"missing_field_accuracy={summary['missing_field_accuracy']:.3f}, "
            f"case_completion_accuracy={summary['case_completion_accuracy']:.3f}, "
            f"triage_success_rate={summary['triage_success_rate']:.3f}"
        )


if __name__ == "__main__":
    main()
