#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0,"tools")
from evaluate_full_day import evaluate, read_jsonl

rules=read_jsonl(Path("artifacts/full_activation_rules_v1.jsonl"))
assert len(rules)==293
ids=[x["id"] for x in rules]
assert len(set(ids))==293
assert sum(x.get("rule_origin")=="remaining_scope_constrained_v1" for x in rules)==130
assert sum(x.get("rule_origin")!="remaining_scope_constrained_v1" for x in rules)==163
for r in rules:
    text=json.dumps(r,ensure_ascii=False)
    assert "target_count" not in text
    assert "daily_limit" not in text
    assert r.get("activation_signals")
    assert r.get("suppression_signals")
    assert r.get("close_condition")
    assert r.get("evidence_rule",{}).get("claim_ceiling")
    assert r.get("maturity_ceiling")=="shadow_only_not_active_reliance"

profile=json.loads(Path("data/full_activation_fixture_day_v1.json").read_text(encoding="utf-8"))["profile"]
zero=evaluate(rules,{"date":"2026-09-05","profile":profile,"signals":{}})
assert zero["candidates"]==[]

fixture=json.loads(Path("data/full_activation_fixture_day_v1.json").read_text(encoding="utf-8"))
out=evaluate(rules,fixture)
by_id={x["id"]:x for x in out["candidates"]}
assert by_id["ADMIN-005"]["layer"]=="now"
assert by_id["PLAY-004"]["layer"]=="routine"
assert by_id["EMG-004"]["layer"]=="review"
assert "GROW-006" in by_id
assert "CLEAN-014" not in by_id
supp={x["id"]:x["reason"] for x in out["suppressed"]}
assert supp["CLEAN-014"]=="feature_gate_all"
assert len(out["candidates"]) < len(rules)
print("full activation rules validation: PASS")
print(out["counts"])
