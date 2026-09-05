#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

catalog_rows = [json.loads(line) for line in Path("artifacts/responsibility_catalog_v2.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
catalog = {row["id"]: row for row in catalog_rows}
pack = json.loads(Path("artifacts/activation_rules_core_v2.json").read_text(encoding="utf-8"))
rules = pack["rules"]
bundles = json.loads(Path("artifacts/surface_bundles_v2.json").read_text(encoding="utf-8"))

assert pack["schema_version"] == 2
assert pack["catalog_item_count"] == 294
assert len(rules) == pack["rule_count"]
assert len({r["rule_id"] for r in rules}) == len(rules)
assert pack["layer_policy"] == "catalog_type_R_forces_routine"
assert set(bundles["rules"]) == {r["rule_id"] for r in rules}
assert bundles["unmatched_rule_ids"] == []

referenced = set()
layer_counts = Counter()
for rule in rules:
    assert rule["maturity"] == "experiment_ready", rule["rule_id"]
    assert rule["description"].strip()
    serialized = json.dumps(rule, ensure_ascii=False)
    for banned in ("target_count", "daily_limit", "fixed_slot", "goal_count"):
        assert banned not in serialized, (rule["rule_id"], banned)
    for emission in rule["emit"]:
        item_id = emission["id"]
        assert item_id in catalog, (rule["rule_id"], item_id)
        referenced.add(item_id)
        layer_counts[emission["layer"]] += 1
        if "R" in catalog[item_id]["type"].split("/"):
            assert emission["layer"] == "routine", (rule["rule_id"], item_id, emission["layer"])

assert referenced == set(catalog), f"catalog items without an activation rule: {sorted(set(catalog)-referenced)}"
assert pack["unreferenced_catalog_item_ids"] == []

health_safety = {item_id for item_id, meta in catalog.items() if "S" in meta["type"].split("/")}
assert health_safety <= referenced
assert len(health_safety) == 43

# High-impact user-facing roots must have explicit bundle patterns, not generic fallbacks.
high_impact_roots = ("routine.", "infant.", "health.", "daycare.", "safety.", "family.")
for rule_id in bundles.get("root_fallback_rule_ids", []):
    assert not rule_id.startswith(high_impact_roots), f"high-impact rule uses root fallback: {rule_id}"

assert all(layer_counts[layer] > 0 for layer in ("now", "today", "routine", "review"))

normalizations = pack.get("routine_layer_normalizations", [])
for row in normalizations:
    assert row["to_layer"] == "routine"
    assert "R" in catalog[row["item_id"]]["type"].split("/")

print("activation rules v2 r2 validation: PASS")
print(f"rules={len(rules)} referenced_items={len(referenced)}/294 health_safety={len(health_safety)}")
print("layer_emissions", dict(layer_counts), "routine_normalizations", len(normalizations), "root_fallbacks", len(bundles.get("root_fallback_rule_ids", [])))
