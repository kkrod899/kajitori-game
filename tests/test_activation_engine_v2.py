#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


payload = json.loads(Path("artifacts/activation_engine_simulation_v2.json").read_text(encoding="utf-8"))
assert payload["synthetic"] is True
reports = {report["scenario_id"]: report["result"] for report in payload["reports"]}
assert set(reports) == {
    "normal_weekday",
    "high_load_heat_weekday",
    "low_load_weekend",
    "winter_disruption",
    "feature_gate_no_daycare_no_car",
}

normal = reports["normal_weekday"]
high = reports["high_load_heat_weekday"]
low = reports["low_load_weekend"]
winter = reports["winter_disruption"]
feature = reports["feature_gate_no_daycare_no_car"]

# Variable load; no fixed-three quota.
assert normal["card_counts"]["now"] == 2
assert 8 <= normal["card_counts"]["today"] <= 18
assert high["card_counts"]["now"] > normal["card_counts"]["now"]
assert high["card_counts"]["today"] >= normal["card_counts"]["today"]
assert low["card_counts"]["now"] == 0
assert low["card_counts"]["today"] == 0
assert winter["card_counts"]["now"] >= 1
assert len({normal["card_counts"]["today"], high["card_counts"]["today"], low["card_counts"]["today"]}) >= 3

# Atomic coverage is preserved but user-facing cards group complete loops.
for result in reports.values():
    assert result["total_atoms"] >= result["total_cards"]
    atom_ids = []
    for layer in ("now", "today", "routine", "review"):
        atom_ids.extend(item["id"] for item in result["layers"][layer])
        card_ids = [card["card_id"] for card in result["cards"][layer]]
        assert len(card_ids) == len(set(card_ids))
    assert len(atom_ids) == len(set(atom_ids))
    card_member_ids = {
        item_id
        for layer in result["cards"].values()
        for card in layer
        for item_id in card["member_ids"]
    }
    assert set(atom_ids) == card_member_ids

normal_daycare_card = next(card for card in normal["cards"]["today"] if card["card_id"] == "daycare.tomorrow_ready")
assert normal_daycare_card["member_count"] >= 6

# Raw facts, not responsibility IDs, drive discovery.
scenario_payload = json.loads(Path("artifacts/experiment_raw_state_scenarios_v2.json").read_text(encoding="utf-8"))
assert all("activations" not in scenario for scenario in scenario_payload["scenarios"])
vaccination_card = next(card for card in high["cards"]["now"] if card["card_id"] == "health.vaccination.appointment")
assert set(vaccination_card["member_ids"]) == {"CHD-MED-003", "PLAN-005", "CHD-MED-007"}

# Seasonal split works.
high_ids = {item["id"] for layer in high["layers"].values() for item in layer}
winter_ids = {item["id"] for layer in winter["layers"].values() for item in layer}
assert "SAFE-018" in high_ids
assert "SAFE-019" not in high_ids
assert "SAFE-019" in winter_ids
assert "SAFE-018" not in winter_ids

# Feature gates override contradictory raw state.
feature_ids = {item["id"] for layer in feature["layers"].values() for item in layer}
assert not any(item_id.startswith("DAYCARE-") for item_id in feature_ids)
assert "SAFE-011" not in feature_ids
assert "GROW-005" not in feature_ids
assert "INF-FEED-008" not in feature_ids
assert "OLD-DAILY-001" not in feature_ids

# All health/safety items are covered by the active rule pack.
coverage = normal["coverage"]
assert coverage["catalog_items"] == 294
assert coverage["rule_referenced_items"] >= 170
assert coverage["health_safety_rule_referenced_items"] == coverage["health_safety_catalog_items"] == 43

# Directly verify boundary suppression with a deliberately malformed test rule.
spec = importlib.util.spec_from_file_location("engine_v2", "tools/simulate_activation_engine_v2.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
catalog = read_jsonl("artifacts/responsibility_catalog_v2.jsonl")
profile = json.loads(Path("data/experiment_household_profile_v1.json").read_text(encoding="utf-8"))
review_payload = json.loads(Path("data/health_safety_review_v2.json").read_text(encoding="utf-8"))
review = {row["id"]: row for row in review_payload["items"]}
boundaries = json.loads(Path("data/health_safety_boundaries_v2.json").read_text(encoding="utf-8"))["items"]
bad_pack = {
    "rule_maturity_required": "experiment_ready",
    "rules": [{
        "rule_id": "test.malformed_symptom_rule",
        "maturity": "experiment_ready",
        "profile_all_tags": ["infant"],
        "profile_config_equals": {},
        "when": {"path": "children.infant.health.symptom_changed", "op": "truthy"},
        "emit": [{"id": "CHD-MED-008", "layer": "now", "reason": "test"}]
    }]
}
bad_state = {
    "date": "2026-09-10",
    "children": {"infant": {"health": {"symptom_changed": True}}}
}
bad_bundle = {
    "test.malformed_symptom_rule": {
        "bundle_id": "test.symptom",
        "label": "test",
        "close_condition": "test"
    }
}
result = engine.derive_candidates(catalog, profile, bad_state, bad_pack, review, boundaries, bad_bundle)
assert result["total_atoms"] == 0
assert result["suppressed"][0]["id"] == "CHD-MED-008"
assert result["suppressed"][0]["reason"] == "boundary_context_missing"
assert "children.infant.health.observed_at" in result["suppressed"][0]["missing_paths"]

# A blocking health review status also suppresses.
blocked_review = copy.deepcopy(review)
blocked_review["SAFE-018"]["status"] = "REWRITE_OR_SPLIT"
heat_rule = {
    "rule_maturity_required": "experiment_ready",
    "rules": [{
        "rule_id": "test.heat",
        "maturity": "experiment_ready",
        "profile_all_tags": ["has_child"],
        "profile_config_equals": {},
        "when": {"path": "context.weather.official_heat_alert_or_high_wbgt", "op": "truthy"},
        "emit": [{"id": "SAFE-018", "layer": "now", "reason": "test"}]
    }]
}
heat_state = {"date": "2026-09-10", "context": {"weather": {"official_heat_alert_or_high_wbgt": True}}}
heat_bundle = {"test.heat": {"bundle_id": "test.heat", "label": "test", "close_condition": "test"}}
blocked = engine.derive_candidates(catalog, profile, heat_state, heat_rule, blocked_review, boundaries, heat_bundle)
assert blocked["total_atoms"] == 0
assert blocked["suppressed"][0]["reason"] == "health_safety_review_blocked"

print("activation engine v2 validation: PASS")
for key in ("normal_weekday", "high_load_heat_weekday", "low_load_weekend", "winter_disruption"):
    print(key, reports[key]["card_counts"], "atoms", reports[key]["total_atoms"])
