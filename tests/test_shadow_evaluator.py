#!/usr/bin/env python3
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("shadow_eval", Path("tools/evaluate_shadow_test.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(rid, *, needed=True, surfaced=True, kind="management", risk="standard", timing="on_time", discovery="self", partner=False, closed=True, duplicate=False, overclaim=False, layer="today", label="synthetic responsibility"):
    return {
        "date": "2026-09-01",
        "responsibility_id": rid,
        "actual_label": label,
        "responsibility_kind": kind,
        "risk_class": risk,
        "actual_needed": needed,
        "surfaced": surfaced,
        "surfaced_layer": layer if surfaced else None,
        "timing_assessment": timing,
        "source_of_discovery": discovery,
        "partner_prompted": partner,
        "loop_closed": closed,
        "duplicate_or_granular": duplicate,
        "evidence_overclaim": overclaim,
        "notes": "synthetic test row"
    }


rows = [
    row("A-001"),
    row("A-002", surfaced=False, timing="not_surfaced", discovery="partner", partner=True),
    row("A-003", surfaced=False, timing="not_surfaced", risk="hard_deadline", discovery="partner", partner=True),
    row("A-004", risk="health_safety", timing="too_late", layer="now"),
    row("A-005", needed=False, surfaced=True, timing="not_applicable", closed=False),
    row(None, label="masterに無かった家庭運営"),
    row("A-007", closed=False),
    row("A-008", duplicate=True),
    row("A-009", kind="routine", layer="routine"),
    row("A-010", overclaim=True),
]

for i, r in enumerate(rows, start=1):
    mod.validate_row(r, i)

result = mod.evaluate(rows)
assert result["status"] == "BLOCKED"
assert result["actual_needed_count"] == 9
assert result["surfaced_count"] == 8
assert result["management_actual_count"] == 8
assert result["management_miss_count"] == 2
assert result["management_miss_rate"] == 0.25
assert result["unnecessary_surfaced_count"] == 1
assert result["noise_rate"] == 0.125
assert result["timing_error_count"] == 1
assert result["timing_error_rate"] == round(1/7, 4)
assert result["critical_miss_count"] == 1
assert result["hard_deadline_miss_count"] == 1
assert result["health_safety_miss_count"] == 0
assert result["partner_prompt_dependency_count"] == 2
assert result["close_loop_failure_count"] == 1
assert result["master_gap_count"] == 1
assert result["duplicate_or_granular_count"] == 1
assert result["evidence_overclaim_count"] == 1
assert result["hard_gate_blockers"] == ["critical_miss", "hard_deadline_miss", "evidence_overclaim"]

clean = [
    row("B-001"),
    row("B-002", risk="health_safety", layer="now"),
    row("B-003", needed=False, timing="not_applicable", closed=False),
]
for i, r in enumerate(clean, start=1):
    mod.validate_row(r, i)
clean_result = mod.evaluate(clean)
assert clean_result["status"] == "BASELINE_COMPLETE_WITH_GAPS"
assert clean_result["hard_gate_blockers"] == []
assert clean_result["critical_miss_count"] == 0
assert clean_result["evidence_overclaim_count"] == 0

# Contract validation: needed+not-surfaced cannot pretend to be on-time.
bad = row("BAD", surfaced=False, timing="on_time")
try:
    mod.validate_row(bad, 1)
except ValueError:
    pass
else:
    raise AssertionError("invalid shadow row was accepted")

print("shadow evaluator validation: PASS")
