#!/usr/bin/env python3
import json
import re
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def walk_conditions(node):
    if "all" in node:
        for child in node["all"]:
            yield from walk_conditions(child)
    elif "any" in node:
        for child in node["any"]:
            yield from walk_conditions(child)
    elif "not" in node:
        yield from walk_conditions(node["not"])
    else:
        yield node


catalog = read_jsonl("artifacts/responsibility_catalog_v2.jsonl")
by_id = {row["id"]: row for row in catalog}
pack = json.loads(Path("artifacts/activation_rules_core_v2.json").read_text(encoding="utf-8"))
bundles = json.loads(Path("artifacts/surface_bundles_v2.json").read_text(encoding="utf-8"))["rules"]
registry = json.loads(Path("artifacts/raw_state_field_registry_v2.json").read_text(encoding="utf-8"))
registry_paths = {field["path"] for field in registry["fields"]}

rules = pack["rules"]
rule_ids = [rule["rule_id"] for rule in rules]
assert len(rules) == 84
assert len(rule_ids) == len(set(rule_ids))
assert set(rule_ids) == set(bundles)

referenced = set()
condition_paths = set()
for rule in rules:
    assert rule["maturity"] == "experiment_ready"
    assert rule["emit"], rule["rule_id"]
    leaves = list(walk_conditions(rule["when"]))
    assert leaves, rule["rule_id"]
    for leaf in leaves:
        assert leaf["path"] in registry_paths, (rule["rule_id"], leaf["path"])
        assert not re.search(r"(?:^|\.)(?:INF|CHD|SAFE|DAYCARE|FOOD|KIT|LAUN|CLEAN|SUP|WASTE|PLAN|ADMIN|HOME|EMG|FAM|GROW|PLAY)-", leaf["path"])
        condition_paths.add(leaf["path"])
    for emission in rule["emit"]:
        assert emission["id"] in by_id, (rule["rule_id"], emission["id"])
        assert emission["layer"] in {"now", "today", "routine", "review"}
        referenced.add(emission["id"])
    bundle = bundles[rule["rule_id"]]
    assert bundle["bundle_id"].strip()
    assert bundle["label"].strip()
    assert bundle["close_condition"].strip()

assert len(referenced) >= 170
health_safety_ids = {row["id"] for row in catalog if "S" in row["type"].split("/")}
assert referenced & health_safety_ids == health_safety_ids, sorted(health_safety_ids - referenced)
assert registry["field_count"] == len(registry_paths)
assert registry["field_count"] >= 130

for field in registry["fields"]:
    assert field["source_class"] != "unknown", field["path"]
    assert field["privacy_class"] in {"sensitive_local_only", "private_local_only", "local_operational"}
    assert field["absence_semantics"].startswith("unknown_or_not_observed")

serialized = json.dumps(pack, ensure_ascii=False)
assert "target_count" not in serialized
assert "daily_limit" not in serialized
assert "goal_count" not in serialized

print("activation rules v2 validation: PASS")
print(f"rules={len(rules)} referenced={len(referenced)} health_safety={len(health_safety_ids)} raw_fields={registry['field_count']}")
