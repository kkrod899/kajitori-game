#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def condition_paths(node: dict) -> list[tuple[str, str]]:
    if "all" in node:
        out = []
        for child in node["all"]:
            out.extend(condition_paths(child))
        return out
    if "any" in node:
        out = []
        for child in node["any"]:
            out.extend(condition_paths(child))
        return out
    if "not" in node:
        return condition_paths(node["not"])
    return [(node["path"], node["op"])]


def source_class(path: str) -> str:
    if path.startswith("context.weather."):
        return "official_external_state"
    if path.startswith("events."):
        return "calendar_provider_or_local_record"
    if path.startswith("daycare."):
        return "daycare_or_household_local_record"
    if path.startswith("children."):
        return "caregiver_observation"
    if path.startswith("family."):
        return "adult_self_report_or_household_record"
    if path.startswith("household."):
        return "household_observation_or_config"
    if path.startswith("profile_runtime."):
        return "runtime_household_feature"
    if path.startswith("context."):
        return "current_context"
    return "unknown"


def privacy_class(path: str) -> str:
    if path.startswith("children.") or path.startswith("events.medical") or path.startswith("events.vaccination") or path.startswith("events.health_check"):
        return "sensitive_local_only"
    if path.startswith("family."):
        return "private_local_only"
    if path.startswith("household.local_area"):
        return "private_local_only"
    return "local_operational"


def expected_value_type(ops: set[str]) -> str:
    if ops & {"lt", "lte", "gt", "gte"}:
        return "number"
    if ops & {"truthy", "falsy"}:
        return "boolean_or_presence"
    if ops & {"in", "not_in"}:
        return "enum"
    if ops & {"exists", "not_exists"}:
        return "timestamp_or_value"
    return "scalar"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="artifacts/activation_rules_core_v2.json")
    ap.add_argument("--boundaries", default="data/health_safety_boundaries_v2.json")
    ap.add_argument("--out", default="artifacts/raw_state_field_registry_v2.json")
    args = ap.parse_args()

    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    boundaries = json.loads(Path(args.boundaries).read_text(encoding="utf-8"))["items"]

    usage: dict[str, dict] = defaultdict(lambda: {"operators": set(), "rule_ids": set(), "boundary_item_ids": set()})
    for rule in rules["rules"]:
        for path, op in condition_paths(rule["when"]):
            usage[path]["operators"].add(op)
            usage[path]["rule_ids"].add(rule["rule_id"])

    for item_id, boundary in boundaries.items():
        for path in boundary["required_context_paths"]:
            usage[path]["boundary_item_ids"].add(item_id)

    fields = []
    for path in sorted(usage):
        meta = usage[path]
        fields.append({
            "path": path,
            "source_class": source_class(path),
            "privacy_class": privacy_class(path),
            "expected_value_type": expected_value_type(meta["operators"]),
            "operators": sorted(meta["operators"]),
            "used_by_rules": sorted(meta["rule_ids"]),
            "required_by_health_safety_boundaries": sorted(meta["boundary_item_ids"]),
            "absence_semantics": "unknown_or_not_observed; never infer false for health/safety"
        })

    payload = {
        "schema_version": 2,
        "description": "activation engine v2が読むraw-state field registry。実在家庭データは含まない。",
        "field_count": len(fields),
        "fields": fields
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "fields": len(fields),
        "sensitive_local_only": sum(x["privacy_class"] == "sensitive_local_only" for x in fields),
        "boundary_paths": sum(bool(x["required_by_health_safety_boundaries"]) for x in fields)
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
