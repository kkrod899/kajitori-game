#!/usr/bin/env python3
import copy
import importlib.util
import json
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]

payload = json.loads(Path("artifacts/activation_engine_v2.json").read_text(encoding="utf-8"))
assert payload["schema_version"] == 2
assert payload["engine_version"] == "v2-r2"
assert payload["fixed_target_count"] is None
reports = {r["id"]: r for r in payload["reports"]}
assert set(reports) == {"normal_weekday_v2", "high_load_weekday_v2", "recovery_weekend_v2", "winter_weather_outing_v2"}

scenario_text = Path("data/experiment_raw_state_scenarios_v2.json").read_text(encoding="utf-8")
assert '"activations"' not in scenario_text

normal = reports["normal_weekday_v2"]
high = reports["high_load_weekday_v2"]
recovery = reports["recovery_weekend_v2"]
winter = reports["winter_weather_outing_v2"]

assert high["counts"]["now"] > normal["counts"]["now"]
assert recovery["counts"]["now"] == 0
assert winter["counts"]["now"] > 0
assert len({normal["counts"]["today"], high["counts"]["today"], recovery["counts"]["today"]}) >= 2
assert high["atomic_total"] > recovery["atomic_total"]

high_ids = {x["id"] for x in high["atomic_candidates"]}
winter_ids = {x["id"] for x in winter["atomic_candidates"]}
assert "SAFE-018" in high_ids
assert "SAFE-019" not in high_ids
assert "SAFE-019" in winter_ids
assert "SAFE-018" not in winter_ids
assert "CHD-MED-003" in high_ids
assert "FAM-004" in high_ids
assert "DAYCARE-008" in normal["atomic_candidates"][0:len(normal["atomic_candidates"])] or "DAYCARE-008" in {x["id"] for x in normal["atomic_candidates"]}

for report in reports.values():
    atom_ids = [x["id"] for x in report["atomic_candidates"]]
    assert len(atom_ids) == len(set(atom_ids)), report["id"]
    assert report["suppressed_health_safety"] == [], report["suppressed_health_safety"]
    card_atomic_ids = [item_id for card in report["cards"] for item_id in card["atomic_ids"]]
    assert sorted(card_atomic_ids) == sorted(atom_ids)
    assert sum(report["counts"].values()) == len(atom_ids)
    assert sum(report["card_counts"].values()) == len(report["cards"])
    assert report["rule_evaluation"]["fired"] > 0
    assert report["card_total"] <= report["atomic_total"]

assert any(r["card_total"] < r["atomic_total"] for r in reports.values()), "surface bundling did not reduce card count"

spec = importlib.util.spec_from_file_location("activation_engine_v2r2", "tools/simulate_activation_engine_v2r2.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
catalog = read_jsonl("artifacts/responsibility_catalog_v2.jsonl")
rules = json.loads(Path("artifacts/activation_rules_core_v2.json").read_text(encoding="utf-8"))["rules"]
profile = json.loads(Path("data/experiment_household_profile_v1.json").read_text(encoding="utf-8"))
scenario_payload = json.loads(Path("data/experiment_raw_state_scenarios_v2.json").read_text(encoding="utf-8"))
review = {x["id"]: x for x in json.loads(Path("data/health_safety_review_v2.json").read_text(encoding="utf-8"))["items"]}
boundaries = {x["id"]: x for x in json.loads(Path("data/health_safety_boundaries_v2.json").read_text(encoding="utf-8"))["items"]}
bundles = json.loads(Path("artifacts/surface_bundles_v2.json").read_text(encoding="utf-8"))["rules"]

# A required health/safety boundary input missing at decision time must suppress the candidate.
high_scenario = next(x for x in scenario_payload["scenarios"] if x["id"] == "high_load_weekday_v2")
missing_boundary = copy.deepcopy(high_scenario)
del missing_boundary["state"]["events"]["vaccination"]["appointment_at"]
result = module.derive(catalog, rules, profile, missing_boundary, review, boundaries, bundles)
result_ids = {x["id"] for x in result["atomic_candidates"]}
assert "CHD-MED-003" not in result_ids
suppressed = {x["item_id"]: x for x in result["suppressed_health_safety"]}
assert "CHD-MED-003" in suppressed
assert "events.vaccination.appointment_at" in suppressed["CHD-MED-003"]["missing_boundary_paths"]

# Missing is unknown, not false. Removing a false-valued field must not fire a falsy rule.
normal_scenario = next(x for x in scenario_payload["scenarios"] if x["id"] == "normal_weekday_v2")
missing_dinner_state = copy.deepcopy(normal_scenario)
del missing_dinner_state["state"]["household"]["food"]["dinner_plan_decided"]
result = module.derive(catalog, rules, profile, missing_dinner_state, review, boundaries, bundles)
result_ids = {x["id"] for x in result["atomic_candidates"]}
assert "FOOD-003" not in result_ids

# Raw state inputs must not be mutated by derivation.
original = copy.deepcopy(high_scenario)
module.derive(catalog, rules, profile, high_scenario, review, boundaries, bundles)
assert high_scenario == original

print("activation engine v2 r2 validation: PASS")
for key in reports:
    r = reports[key]
    print(key, "atomic", r["counts"], "cards", r["card_counts"], "fired_rules", r["rule_evaluation"]["fired"])
