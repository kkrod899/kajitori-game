#!/usr/bin/env python3
import json
from pathlib import Path

rules = json.loads(Path("artifacts/activation_rules_core_v2.json").read_text(encoding="utf-8"))["rules"]
registry = json.loads(Path("artifacts/raw_state_registry_v2.json").read_text(encoding="utf-8"))
paths = {row["path"]: row for row in registry["fields"]}

assert registry["schema_version"] == 2
assert len(paths) == len(registry["fields"])

rule_paths = set()
def walk(node):
    if "all" in node:
        for child in node["all"]: walk(child)
    elif "any" in node:
        for child in node["any"]: walk(child)
    elif "not" in node:
        walk(node["not"])
    else:
        rule_paths.add(node["path"])

for rule in rules:
    walk(rule["when"])

missing = sorted(rule_paths - set(paths))
assert not missing, missing
for path in rule_paths:
    row = paths[path]
    assert row["privacy"] in {"local_only", "public_context"}
    assert row["source_class"] in {"manual_household_observation", "local_household_config", "official_external_signal"}
    assert row["rules"], path

assert paths["context.weather.official_heat_alert_or_high_wbgt"]["source_class"] == "official_external_signal"
assert paths["context.weather.official_snow_or_blizzard_warning"]["source_class"] == "official_external_signal"
assert paths["context.weather.official_heat_alert_or_high_wbgt"]["privacy"] == "public_context"
assert paths["children.infant.health.observed_at"]["privacy"] == "local_only"

intake = json.loads(Path("data/shadow_intake_spec_v2.json").read_text(encoding="utf-8"))
intake_paths = set()
for section in intake["sections"]:
    for field in section["fields"]:
        intake_paths.add(field["raw_state_path"])
        intake_paths.update(field.get("on_true_set", {}).keys())
        intake_paths.update(field.get("also_set", {}).keys())
missing_intake_paths = sorted(intake_paths - set(paths))
assert not missing_intake_paths, f"intake uses unregistered raw paths: {missing_intake_paths}"

required_visible = sum(1 for section in intake["sections"] for field in section["fields"] if field.get("required") and field.get("visibility") == "morning")
assert required_visible <= intake["burden_budget"]["max_required_visible_fields"], required_visible
assert intake["privacy"]["storage"] == "local_only"

print("raw state registry v2 validation: PASS")
print(f"registered_paths={len(paths)} rule_paths={len(rule_paths)} required_morning_fields={required_visible}")
