#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("shadow_v2", "tools/evaluate_shadow_test_v2.py")
shadow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shadow)


def actual(rid, *, surfaced, risk="standard", card=None, atoms=None, timing=None,
           input_available=True, rule_covered=True, input_gap="none", partner=False,
           closed=True, label=None, overclaim=False, suppressed=None):
    return {
        "date": "2026-09-10",
        "record_scope": "actual_atomic",
        "responsibility_id": rid,
        "actual_label": label or rid or "master gap",
        "candidate_card_id": card if surfaced else None,
        "atomic_responsibility_ids": atoms or ([] if not surfaced else [rid]),
        "responsibility_kind": "management",
        "risk_class": risk,
        "actual_needed": True,
        "surfaced": surfaced,
        "surfaced_layer": "now" if surfaced and risk != "standard" else ("today" if surfaced else None),
        "timing_assessment": timing or ("on_time" if surfaced else "not_surfaced"),
        "source_of_discovery": "partner" if partner else "self",
        "partner_prompted": partner,
        "loop_closed": closed,
        "duplicate_or_granular": False,
        "evidence_overclaim": overclaim,
        "input_available_at_decision_time": input_available,
        "rule_covered": rule_covered,
        "input_gap_type": input_gap,
        "suppressed_reason": suppressed,
        "notes": "synthetic test fixture"
    }


def noise(card, atoms):
    return {
        "date": "2026-09-10",
        "record_scope": "surfaced_card_only",
        "responsibility_id": None,
        "actual_label": "不要だったカード",
        "candidate_card_id": card,
        "atomic_responsibility_ids": atoms,
        "responsibility_kind": "management",
        "risk_class": "standard",
        "actual_needed": False,
        "surfaced": True,
        "surfaced_layer": "today",
        "timing_assessment": "not_applicable",
        "source_of_discovery": "self",
        "partner_prompted": False,
        "loop_closed": True,
        "duplicate_or_granular": False,
        "evidence_overclaim": False,
        "input_available_at_decision_time": True,
        "rule_covered": True,
        "input_gap_type": "not_applicable",
        "suppressed_reason": None,
        "notes": "synthetic noise fixture"
    }


rows = [
    actual("DAYCARE-008", surfaced=True, risk="hard_deadline", card="daycare.deadline", atoms=["DAYCARE-008"]),
    actual("FOOD-003", surfaced=True, card="food.plan", atoms=["FOOD-003", "FOOD-017"], timing="too_late", partner=True, closed=False),
    actual("INF-DIAP-002", surfaced=False, input_available=True, rule_covered=True),
    actual("SUP-003", surfaced=False, input_available=False, rule_covered=True, input_gap="not_integrated"),
    actual(None, surfaced=False, input_available=True, rule_covered=False, label="園の臨時持ち物"),
    noise("home.unneeded", ["CLEAN-014"]),
]
result = shadow.evaluate(rows)
assert result["status"] == "BASELINE_COMPLETE_WITH_GAPS"
assert result["management_miss_count"] == 3
assert result["engine_miss_count"] == 1
assert result["input_gap_count"] == 1
assert result["rule_gap_count"] == 1
assert result["surfaced_card_count"] == 3
assert result["relevant_card_count"] == 2
assert result["noisy_card_count"] == 1
assert result["card_noise_rate"] == round(1 / 3, 4)
assert result["timing_error_count"] == 1
assert result["partner_prompt_dependency_count"] == 1
assert result["close_loop_failure_count"] == 1
assert result["master_gap_count"] == 1
assert result["hard_gate_blockers"] == []

critical_rows = rows + [
    actual("SAFE-002", surfaced=False, risk="health_safety", input_available=False, rule_covered=True, input_gap="not_observed"),
    actual("CHD-MED-003", surfaced=False, risk="hard_deadline", input_available=True, rule_covered=True),
    actual("SAFE-019", surfaced=False, risk="health_safety", input_available=True, rule_covered=False),
    actual("SAFE-001", surfaced=True, risk="health_safety", card="safety.sleep", atoms=["SAFE-001"], overclaim=True),
]
blocked = shadow.evaluate(critical_rows)
assert blocked["status"] == "BLOCKED"
assert set(blocked["hard_gate_blockers"]) == {
    "critical_engine_miss", "critical_input_miss", "critical_rule_gap", "evidence_overclaim"
}
assert blocked["critical_engine_miss_count"] == 1
assert blocked["critical_input_miss_count"] == 1
assert blocked["critical_rule_gap_count"] == 1
assert blocked["evidence_overclaim_count"] == 1

# The public schema and executable validation must agree on the required fields.
schema = json.loads(Path("data/shadow_observation_schema_v2.json").read_text(encoding="utf-8"))
assert set(schema["required_fields"]) == shadow.REQUIRED
assert schema["privacy_rule"] == "responses_local_only_never_commit_to_public_repo"

# JSONL loading exercises row-level validation.
with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "obs.jsonl"
    p.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows) + "\n", encoding="utf-8")
    loaded = shadow.load_jsonl(p)
    assert len(loaded) == len(rows)

bad = dict(rows[0])
bad["surfaced"] = False
try:
    shadow.validate_row(bad, 1)
except ValueError as exc:
    assert "null card/layer" in str(exc)
else:
    raise AssertionError("invalid shadow row was accepted")

print("shadow evaluator v2 validation: PASS")
