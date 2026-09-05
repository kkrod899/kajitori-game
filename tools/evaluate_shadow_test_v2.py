#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

VALID_SCOPE = {"actual_atomic", "surfaced_card_only"}
VALID_KIND = {"management", "routine"}
VALID_RISK = {"standard", "hard_deadline", "health_safety"}
VALID_LAYER = {"now", "today", "routine", "review", None}
VALID_TIMING = {"on_time", "too_early", "too_late", "not_surfaced", "not_applicable"}
VALID_DISCOVERY = {"self", "partner", "environment", "calendar", "daycare", "official_notice", "other"}
VALID_INPUT_GAP = {"none", "not_observed", "not_integrated", "unknown_feature", "not_applicable"}

REQUIRED = {
    "date", "record_scope", "actual_needed", "surfaced", "responsibility_kind", "risk_class",
    "timing_assessment", "source_of_discovery", "partner_prompted", "loop_closed",
    "duplicate_or_granular", "evidence_overclaim", "input_available_at_decision_time",
    "rule_covered", "input_gap_type"
}


def load_jsonl(path: Path):
    rows = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {idx}: invalid JSON: {exc}") from exc
        validate_row(row, idx)
        rows.append(row)
    if not rows:
        raise ValueError("shadow observation file is empty")
    return rows


def validate_row(row, idx):
    missing = sorted(REQUIRED - set(row))
    if missing:
        raise ValueError(f"line {idx}: missing fields {missing}")
    if row["record_scope"] not in VALID_SCOPE:
        raise ValueError(f"line {idx}: invalid record_scope")
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
    if row["input_gap_type"] not in VALID_INPUT_GAP:
        raise ValueError(f"line {idx}: invalid input_gap_type")
    for key in (
        "actual_needed", "surfaced", "partner_prompted", "loop_closed", "duplicate_or_granular",
        "evidence_overclaim", "input_available_at_decision_time", "rule_covered"
    ):
        if not isinstance(row[key], bool):
            raise ValueError(f"line {idx}: {key} must be boolean")

    atoms = row.get("atomic_responsibility_ids", [])
    if not isinstance(atoms, list) or any(not isinstance(x, str) or not x for x in atoms):
        raise ValueError(f"line {idx}: atomic_responsibility_ids must be a string array")
    if len(atoms) != len(set(atoms)):
        raise ValueError(f"line {idx}: duplicate atomic_responsibility_ids")

    if row["record_scope"] == "actual_atomic" and not row["actual_needed"]:
        raise ValueError(f"line {idx}: actual_atomic requires actual_needed=true")
    if row["record_scope"] == "surfaced_card_only":
        if row["actual_needed"] or not row["surfaced"]:
            raise ValueError(f"line {idx}: surfaced_card_only requires actual_needed=false and surfaced=true")
        if row.get("responsibility_id") is not None:
            raise ValueError(f"line {idx}: surfaced_card_only requires responsibility_id=null")
        if not row.get("candidate_card_id") or not atoms:
            raise ValueError(f"line {idx}: surfaced_card_only requires card id and atomic ids")

    if not row["surfaced"]:
        if row.get("surfaced_layer") is not None or row.get("candidate_card_id") is not None or atoms:
            raise ValueError(f"line {idx}: surfaced=false requires null card/layer and empty atom list")
    else:
        if not row.get("candidate_card_id") or row.get("surfaced_layer") is None or not atoms:
            raise ValueError(f"line {idx}: surfaced=true requires card id, layer, and atomic ids")
        rid = row.get("responsibility_id")
        if row["record_scope"] == "actual_atomic" and rid is not None and rid not in atoms:
            raise ValueError(f"line {idx}: surfaced actual responsibility must be in card atoms")

    if row["actual_needed"]:
        if not row.get("actual_label", "").strip():
            raise ValueError(f"line {idx}: actual needed observation requires actual_label")
        if not row["surfaced"] and row["timing_assessment"] != "not_surfaced":
            raise ValueError(f"line {idx}: needed+not surfaced requires timing=not_surfaced")
        if row["surfaced"] and row["timing_assessment"] not in {"on_time", "too_early", "too_late"}:
            raise ValueError(f"line {idx}: needed+surfaced requires an observed timing assessment")
        if row["input_available_at_decision_time"] and row["input_gap_type"] != "none":
            raise ValueError(f"line {idx}: available input requires input_gap_type=none")
        if not row["input_available_at_decision_time"] and row["input_gap_type"] not in {"not_observed", "not_integrated", "unknown_feature"}:
            raise ValueError(f"line {idx}: unavailable input requires a concrete input gap type")
    else:
        if row["timing_assessment"] != "not_applicable" or row["input_gap_type"] != "not_applicable":
            raise ValueError(f"line {idx}: unnecessary card requires not_applicable timing/input gap")


def rate(num, den):
    return round(num / den, 4) if den else 0.0


def classify_miss(row):
    if row["surfaced"]:
        return None
    if not row["rule_covered"]:
        return "rule_gap"
    if not row["input_available_at_decision_time"]:
        return "input_gap"
    return "engine_miss"


def evaluate(rows):
    actual = [r for r in rows if r["record_scope"] == "actual_atomic"]
    missed = [r for r in actual if not r["surfaced"]]
    management_actual = [r for r in actual if r["responsibility_kind"] == "management"]
    management_missed = [r for r in management_actual if not r["surfaced"]]
    needed_surfaced = [r for r in actual if r["surfaced"]]
    timing_errors = [r for r in needed_surfaced if r["timing_assessment"] in {"too_early", "too_late"}]

    miss_groups = {"rule_gap": [], "input_gap": [], "engine_miss": []}
    for row in missed:
        miss_groups[classify_miss(row)].append(row)

    critical = [r for r in missed if r["risk_class"] in {"hard_deadline", "health_safety"}]
    critical_groups = {"rule_gap": [], "input_gap": [], "engine_miss": []}
    for row in critical:
        critical_groups[classify_miss(row)].append(row)

    card_rows = defaultdict(list)
    for row in rows:
        if row["surfaced"]:
            card_rows[(row["date"], row["candidate_card_id"])].append(row)
    noisy_cards = [key for key, group in card_rows.items() if not any(r["actual_needed"] for r in group)]
    relevant_cards = [key for key, group in card_rows.items() if any(r["actual_needed"] for r in group)]

    partner_prompt = [r for r in actual if r["partner_prompted"]]
    loop_failures = [r for r in actual if not r["loop_closed"]]
    master_gaps = [r for r in actual if r.get("responsibility_id") is None]
    duplicates = [r for r in rows if r["duplicate_or_granular"]]
    overclaims = [r for r in rows if r["evidence_overclaim"]]

    blockers = []
    if critical_groups["engine_miss"]:
        blockers.append("critical_engine_miss")
    if critical_groups["input_gap"]:
        blockers.append("critical_input_miss")
    if critical_groups["rule_gap"]:
        blockers.append("critical_rule_gap")
    if overclaims:
        blockers.append("evidence_overclaim")

    result = {
        "schema_version": 2,
        "status": "BLOCKED" if blockers else "BASELINE_COMPLETE_WITH_GAPS",
        "hard_gate_blockers": blockers,
        "observation_count": len(rows),
        "days_observed": len({r["date"] for r in rows}),
        "actual_atomic_count": len(actual),
        "management_actual_count": len(management_actual),
        "atomic_miss_count": len(missed),
        "atomic_miss_rate": rate(len(missed), len(actual)),
        "management_miss_count": len(management_missed),
        "management_miss_rate": rate(len(management_missed), len(management_actual)),
        "rule_gap_count": len(miss_groups["rule_gap"]),
        "input_gap_count": len(miss_groups["input_gap"]),
        "engine_miss_count": len(miss_groups["engine_miss"]),
        "surfaced_card_count": len(card_rows),
        "relevant_card_count": len(relevant_cards),
        "noisy_card_count": len(noisy_cards),
        "card_noise_rate": rate(len(noisy_cards), len(card_rows)),
        "timing_error_count": len(timing_errors),
        "timing_error_rate": rate(len(timing_errors), len(needed_surfaced)),
        "critical_miss_count": len(critical),
        "critical_engine_miss_count": len(critical_groups["engine_miss"]),
        "critical_input_miss_count": len(critical_groups["input_gap"]),
        "critical_rule_gap_count": len(critical_groups["rule_gap"]),
        "hard_deadline_miss_count": sum(1 for r in critical if r["risk_class"] == "hard_deadline"),
        "health_safety_miss_count": sum(1 for r in critical if r["risk_class"] == "health_safety"),
        "partner_prompt_dependency_count": len(partner_prompt),
        "close_loop_failure_count": len(loop_failures),
        "master_gap_count": len(master_gaps),
        "duplicate_or_granular_count": len(duplicates),
        "evidence_overclaim_count": len(overclaims),
        "input_gap_type_counts": dict(Counter(r["input_gap_type"] for r in miss_groups["input_gap"])),
        "discovery_source_counts": dict(Counter(r["source_of_discovery"] for r in actual)),
        "surfaced_layer_counts": dict(Counter(r["surfaced_layer"] for r in rows if r["surfaced"])),
        "finding_ids": {
            "critical_engine_miss": [r.get("responsibility_id") for r in critical_groups["engine_miss"]],
            "critical_input_miss": [r.get("responsibility_id") for r in critical_groups["input_gap"]],
            "critical_rule_gap": [r.get("responsibility_id") for r in critical_groups["rule_gap"]],
            "engine_miss": [r.get("responsibility_id") for r in miss_groups["engine_miss"]],
            "input_gap": [r.get("responsibility_id") for r in miss_groups["input_gap"]],
            "rule_gap": [r.get("responsibility_id") for r in miss_groups["rule_gap"]],
            "noisy_cards": [card_id for _, card_id in noisy_cards],
            "master_gap_labels": [r.get("actual_label") for r in master_gaps],
            "partner_prompt": [r.get("responsibility_id") for r in partner_prompt],
            "loop_failure": [r.get("responsibility_id") for r in loop_failures]
        }
    }
    return result


def markdown(result):
    lines = ["# SHADOW TEST EVALUATION v2", "", f"Status: **{result['status']}**", ""]
    if result["hard_gate_blockers"]:
        lines += ["Hard gate blockers: " + ", ".join(result["hard_gate_blockers"]), ""]
    lines += [
        "| Metric | Value |",
        "|---|---:|",
        f"| Days observed | {result['days_observed']} |",
        f"| Actual atomic responsibilities | {result['actual_atomic_count']} |",
        f"| Management miss | {result['management_miss_count']} ({result['management_miss_rate']:.2%}) |",
        f"| Rule gap | {result['rule_gap_count']} |",
        f"| Input gap | {result['input_gap_count']} |",
        f"| Engine miss | {result['engine_miss_count']} |",
        f"| Surfaced cards | {result['surfaced_card_count']} |",
        f"| Noisy cards | {result['noisy_card_count']} ({result['card_noise_rate']:.2%}) |",
        f"| Timing error | {result['timing_error_count']} ({result['timing_error_rate']:.2%}) |",
        f"| Critical engine miss | {result['critical_engine_miss_count']} |",
        f"| Critical input miss | {result['critical_input_miss_count']} |",
        f"| Critical rule gap | {result['critical_rule_gap_count']} |",
        f"| Partner prompt dependency | {result['partner_prompt_dependency_count']} |",
        f"| Close-loop failure | {result['close_loop_failure_count']} |",
        f"| Master gap | {result['master_gap_count']} |",
        f"| Duplicate/granular | {result['duplicate_or_granular_count']} |",
        f"| Evidence overclaim | {result['evidence_overclaim_count']} |",
        "",
        "第1期ではsoft metricに任意の合格閾値を当てない。入力不足・rule不足・engine判定不足を分けて修正し、第2期基準を事前登録する。",
        ""
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="shadow observation JSONL v2")
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
