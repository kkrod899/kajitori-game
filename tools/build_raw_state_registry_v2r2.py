#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

BOOLEAN_OPS = {"truthy", "falsy"}
SCALAR_OPS = {"eq", "ne", "lt", "lte", "gt", "gte", "in", "not_in", "contains", "intersects"}


def walk_condition(node: dict, rule_id: str, out: dict) -> None:
    if "all" in node:
        for child in node["all"]:
            walk_condition(child, rule_id, out)
        return
    if "any" in node:
        for child in node["any"]:
            walk_condition(child, rule_id, out)
        return
    if "not" in node:
        walk_condition(node["not"], rule_id, out)
        return
    path = node["path"]
    out[path]["rules"].add(rule_id)
    out[path]["ops"].add(node["op"])
    if "value" in node:
        out[path]["sample_values"].append(node["value"])


def flatten_state(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            yield from flatten_state(child, child_prefix)
    else:
        yield prefix, value


def expected_type(ops: set[str], values: list) -> str:
    if ops and ops <= {"exists", "not_exists"}:
        return "any"
    if ops & BOOLEAN_OPS:
        return "boolean"
    non_null = [v for v in values if v is not None]
    if non_null:
        types = {type(v).__name__ for v in non_null}
        if types <= {"int", "float"}:
            return "number"
        if types == {"bool"}:
            return "boolean"
        if types == {"list"}:
            return "array"
        if types == {"str"}:
            if any("T" in v and ("+" in v or v.endswith("Z")) for v in non_null if isinstance(v, str)):
                return "datetime"
            return "string"
    if ops & SCALAR_OPS:
        return "scalar"
    return "any"


def classify_source(path: str) -> tuple[str, str, str]:
    if path.startswith("context.weather.official_"):
        return "official_external_signal", "public_context", "official_source_adapter"
    if path.startswith("context."):
        return "manual_household_observation", "local_only", "event_context_input"
    if path.startswith("profile_runtime."):
        return "local_household_config", "local_only", "profile_setup"
    if path.startswith(("children.", "family.", "household.", "daycare.", "events.")):
        return "manual_household_observation", "local_only", "shadow_intake_or_event_capture"
    return "manual_household_observation", "local_only", "explicit_input"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="artifacts/activation_rules_core_v2.json")
    ap.add_argument("--boundaries", default="data/health_safety_boundaries_v2.json")
    ap.add_argument("--intake", default="data/shadow_intake_spec_v2.json")
    ap.add_argument("--scenarios", default="data/experiment_raw_state_scenarios_v2.json")
    ap.add_argument("--out", default="artifacts/raw_state_registry_v2.json")
    args = ap.parse_args()

    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))["rules"]
    boundaries = json.loads(Path(args.boundaries).read_text(encoding="utf-8"))["items"]
    intake = json.loads(Path(args.intake).read_text(encoding="utf-8"))
    scenario_payload = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))

    registry = defaultdict(lambda: {
        "rules": set(),
        "boundary_items": set(),
        "intake_fields": set(),
        "ops": set(),
        "sample_values": [],
        "scenario_presence": set(),
    })

    for rule in rules:
        walk_condition(rule["when"], rule["rule_id"], registry)

    for boundary in boundaries:
        for path in boundary.get("required_context_paths", []):
            registry[path]["boundary_items"].add(boundary["id"])
            registry[path]["ops"].add("exists")

    for section in intake.get("sections", []):
        for field in section.get("fields", []):
            field_id = field.get("field_id") or field.get("id") or field.get("label") or "unnamed_intake_field"
            direct = field.get("raw_state_path")
            if direct:
                registry[direct]["intake_fields"].add(field_id)
            for mapping_name in ("on_true_set", "also_set"):
                mapping = field.get(mapping_name, {})
                if isinstance(mapping, dict):
                    for path, value in mapping.items():
                        registry[path]["intake_fields"].add(field_id)
                        registry[path]["sample_values"].append(value)

    for scenario in scenario_payload.get("scenarios", []):
        for path, value in flatten_state(scenario.get("state", {})):
            registry[path]["scenario_presence"].add(scenario["id"])
            registry[path]["sample_values"].append(value)

    fields = []
    for path in sorted(registry):
        row = registry[path]
        source_class, privacy, collection_mode = classify_source(path)
        sample_values = []
        for value in row["sample_values"]:
            if value not in sample_values:
                sample_values.append(value)
            if len(sample_values) >= 8:
                break
        fields.append({
            "path": path,
            "expected_type": expected_type(row["ops"], sample_values),
            "source_class": source_class,
            "privacy": privacy,
            "collection_mode": collection_mode,
            "missing_value_semantics": "unknown_not_false",
            "rules": sorted(row["rules"]),
            "boundary_items": sorted(row["boundary_items"]),
            "intake_fields": sorted(row["intake_fields"]),
            "scenario_presence": sorted(row["scenario_presence"]),
            "operators": sorted(row["ops"]),
            "example_values": sample_values,
        })

    payload = {
        "schema_version": 2,
        "field_count": len(fields),
        "privacy_default": "local_only",
        "missing_value_policy": "Missing is unknown. The engine may not infer safe/complete/false from absence.",
        "fields": fields,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rule_paths = sum(1 for row in fields if row["rules"])
    boundary_paths = sum(1 for row in fields if row["boundary_items"])
    intake_paths = sum(1 for row in fields if row["intake_fields"])
    print(json.dumps({
        "fields": len(fields),
        "rule_paths": rule_paths,
        "boundary_paths": boundary_paths,
        "intake_paths": intake_paths,
        "public_context_fields": sum(1 for row in fields if row["privacy"] == "public_context"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
