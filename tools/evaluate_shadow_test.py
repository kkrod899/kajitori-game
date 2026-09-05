#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

VALID_KIND = {"management", "routine"}
VALID_RISK = {"standard", "hard_deadline", "health_safety"}
VALID_LAYER = {"now", "today", "routine", "review", None}
VALID_TIMING = {"on_time", "too_early", "too_late", "not_surfaced", "not_applicable"}
VALID_DISCOVERY = {"self", "partner", "environment", "calendar", "daycare", "official_notice", "other"}

REQUIRED = {
    "date", "actual_needed", "surfaced", "responsibility_kind", "risk_class",
    "timing_assessment", "source_of_discovery", "partner_prompted", "loop_closed",
    "duplicate_or_granular", "evidence_overclaim"
}


def load_jsonl(path: Path):
    rows = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"line {idx}: invalid JSON: {e}") from e
        validate_row(row, idx)
        rows.append(row)
    return rows


def validate_row(row, idx):
    missing = sorted(REQUIRED - set(row))
    if missing:
        raise ValueError(f"line {idx}: missing fields {missing}")
    if row["responsibility_kind"] not in VALID_KIND:
        raise ValueError(f"line {idx}: invalid responsibility_kind")
    if row["risk_class"] not in VALID_RISK:
        raise ValueError(f"line {idx}: invalid risk_class")
    if row.get("surfaced_layer") not in VALID_LAYER:
        raise ValueError(f"line {idx}: invalid surfaced_layer")
    if row["timing_assessment"] not in VALID_TIMING:
        raise ValueError(f"line {idx}: invalid timing_assessment")
    if row["source_of_discovery"] not in VALID_DISCOVERY:
        raise ValueError(f"line {idx}: invalid source_of_discovery")
    for key in ("actual_needed", "surfaced", "partner_prompted", "loop_closed", "duplicate_or_granular", "evidence_overclaim"):
        if not isinstance(row[key], bool):
            raise ValueError(f"line {idx}: {key} must be boolean")
    if not row["surfaced"] and row.get("surfaced_layer") is not None:
        raise ValueError(f"line {idx}: surfaced=false requires surfaced_layer=null")
    if row["actual_needed"] and not row["surfaced"] and row["timing_assessment"] != "not_surfaced":
        raise ValueError(f"line {idx}: needed+not surfaced requires timing=not_surfaced")
    if not row["actual_needed"] and row["timing_assessment"] != "not_applicable":
        raise ValueError(f"line {idx}: unnecessary observation requires timing=not_applicable")
    if row["actual_needed"] and not row.get("actual_label", "").strip():
        raise ValueError(f"line {idx}: actual needed observation requires actual_label")


def rate(num, den):
    return round(num / den, 4) if den else 0.0


def evaluate(rows):
    actual = [r for r in rows if r["actual_needed"]]
    surfaced = [r for r in rows if r["surfaced"]]
    management_actual = [r for r in actual if r["responsibility_kind"] == "management"]
    management_missed = [r for r in management_actual if not r["surfaced"]]
    unnecessary_surfaced = [r for r in surfaced if not r["actual_needed"]]
    needed_surfaced = [r for r in surfaced if r["actual_needed"]]
    timing_errors = [r for r in needed_surfaced if r["timing_assessment"] in {"too_early", "too_late"}]
    critical_misses = [r for r in actual if not r["surfaced"] and r["risk_class"] in {"hard_deadline", "health_safety"}]
    hard_deadline_misses = [r for r in actual if not r["surfaced"] and r["risk_class"] == "hard_deadline"]
    health_safety_misses = [r for r in actual if not r["surfaced"] and r["risk_class"] == "health_safety"]
    partner_prompt = [r for r in actual if r["partner_prompted"]]
    loop_failures = [r for r in actual if not r["loop_closed"]]
    master_gaps = [r for r in actual if r.get("responsibility_id") is None]
    duplicates = [r for r in rows if r["duplicate_or_granular"]]
    overclaims = [r for r in rows if r["evidence_overclaim"]]

    blockers = []
    if critical_misses:
        blockers.append("critical_miss")
    if hard_deadline_misses:
        blockers.append("hard_deadline_miss")
    if overclaims:
        blockers.append("evidence_overclaim")

    status = "BLOCKED" if blockers else "BASELINE_COMPLETE_WITH_GAPS"

    by_day = Counter(r["date"] for r in rows)
    result = {
        "schema_version": 1,
        "status": status,
        "hard_gate_blockers": blockers,
        "observation_count": len(rows),
        "days_observed": len(by_day),
        "actual_needed_count": len(actual),
        "surfaced_count": len(surfaced),
        "relevant_surfaced_count": len(needed_surfaced),
        "management_actual_count": len(management_actual),
        "management_miss_count": len(management_missed),
        "management_miss_rate": rate(len(management_missed), len(management_actual)),
        "unnecessary_surfaced_count": len(unnecessary_surfaced),
        "noise_rate": rate(len(unnecessary_surfaced), len(surfaced)),
        "timing_error_count": len(timing_errors),
        "timing_error_rate": rate(len(timing_errors), len(needed_surfaced)),
        "critical_miss_count": len(critical_misses),
        "hard_deadline_miss_count": len(hard_deadline_misses),
        "health_safety_miss_count": len(health_safety_misses),
        "partner_prompt_dependency_count": len(partner_prompt),
        "close_loop_failure_count": len(loop_failures),
        "master_gap_count": len(master_gaps),
        "duplicate_or_granular_count": len(duplicates),
        "evidence_overclaim_count": len(overclaims),
        "discovery_source_counts": dict(Counter(r["source_of_discovery"] for r in actual)),
        "surfaced_layer_counts": dict(Counter(str(r.get("surfaced_layer")) for r in surfaced)),
        "finding_ids": {
            "critical_miss": [r.get("responsibility_id") for r in critical_misses],
            "management_miss": [r.get("responsibility_id") for r in management_missed],
            "master_gap_labels": [r.get("actual_label") for r in master_gaps],
            "partner_prompt": [r.get("responsibility_id") for r in partner_prompt],
            "loop_failure": [r.get("responsibility_id") for r in loop_failures]
        }
    }
    return result


def markdown(result):
    lines = ["# SHADOW TEST EVALUATION", ""]
    lines.append(f"Status: **{result['status']}**")
    lines.append("")
    if result["hard_gate_blockers"]:
        lines.append("Hard gate blockers: " + ", ".join(result["hard_gate_blockers"]))
        lines.append("")
    lines.extend([
        "| Metric | Value |",
        "|---|---:|",
        f"| Days observed | {result['days_observed']} |",
        f"| Actual needed | {result['actual_needed_count']} |",
        f"| Management miss | {result['management_miss_count']} ({result['management_miss_rate']:.2%}) |",
        f"| Noise | {result['unnecessary_surfaced_count']} ({result['noise_rate']:.2%}) |",
        f"| Timing error | {result['timing_error_count']} ({result['timing_error_rate']:.2%}) |",
        f"| Critical miss | {result['critical_miss_count']} |",
        f"| Hard deadline miss | {result['hard_deadline_miss_count']} |",
        f"| Health/safety miss | {result['health_safety_miss_count']} |",
        f"| Partner prompt dependency | {result['partner_prompt_dependency_count']} |",
        f"| Close-loop failure | {result['close_loop_failure_count']} |",
        f"| Master gap | {result['master_gap_count']} |",
        f"| Duplicate/granular | {result['duplicate_or_granular_count']} |",
        f"| Evidence overclaim | {result['evidence_overclaim_count']} |",
        ""
    ])
    lines.append("第1期ではsoft metricに合格閾値を自動適用しない。baseline取得後に第2期目標を事前登録する。")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="shadow observation JSONL")
    ap.add_argument("--json-out")
    ap.add_argument("--md-out")
    args = ap.parse_args()
    rows = load_jsonl(Path(args.input))
    result = evaluate(rows)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    if args.md_out:
        Path(args.md_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.md_out).write_text(markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
