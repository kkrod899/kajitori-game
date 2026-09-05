#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ALLOWED_LAYERS = {"now", "today", "routine", "review"}
ALLOWED_OPS = {"exists", "not_exists", "truthy", "falsy", "eq", "ne", "in", "not_in", "lt", "lte", "gt", "gte", "contains", "intersects"}
ALLOWED_MATURITY = {"experiment_ready", "draft", "blocked"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_condition(node: dict, rule_id: str) -> None:
    if not isinstance(node, dict) or not node:
        raise ValueError(f"{rule_id}: when must be a non-empty object")
    compound = set(node) & {"all", "any", "not"}
    if compound:
        if len(compound) != 1 or len(node) != 1:
            raise ValueError(f"{rule_id}: compound condition cannot mix keys: {node}")
        key = next(iter(compound))
        if key == "not":
            validate_condition(node[key], rule_id)
            return
        children = node[key]
        if not isinstance(children, list) or not children:
            raise ValueError(f"{rule_id}: {key} must contain a non-empty list")
        for child in children:
            validate_condition(child, rule_id)
        return

    path = node.get("path")
    op = node.get("op")
    if not isinstance(path, str) or not path.strip() or " " in path:
        raise ValueError(f"{rule_id}: invalid condition path: {path!r}")
    if op not in ALLOWED_OPS:
        raise ValueError(f"{rule_id}: unsupported condition op: {op!r}")
    if op not in {"exists", "not_exists", "truthy", "falsy"} and "value" not in node:
        raise ValueError(f"{rule_id}: op {op} requires value")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts-dir", default="data/activation_rules_v2")
    ap.add_argument("--catalog", default="artifacts/responsibility_catalog_v2.jsonl")
    ap.add_argument("--out", default="artifacts/activation_rules_core_v2.json")
    args = ap.parse_args()

    catalog_rows = read_jsonl(Path(args.catalog))
    catalog = {row["id"]: row for row in catalog_rows}
    if len(catalog) != len(catalog_rows):
        raise SystemExit("duplicate catalog IDs")

    part_paths = sorted(Path(args.parts_dir).glob("*.json"))
    if not part_paths:
        raise SystemExit("no activation rule part files found")

    rules: list[dict] = []
    seen_rule_ids: set[str] = set()
    referenced_ids: set[str] = set()
    normalizations: list[dict] = []
    parts: list[dict] = []

    for path in part_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 2:
            raise SystemExit(f"{path}: schema_version must be 2")
        part_name = payload.get("part")
        source_rules = payload.get("rules")
        if not isinstance(part_name, str) or not part_name:
            raise SystemExit(f"{path}: part is required")
        if not isinstance(source_rules, list) or not source_rules:
            raise SystemExit(f"{path}: rules must be a non-empty list")
        parts.append({"part": part_name, "path": str(path), "rule_count": len(source_rules)})

        for original in source_rules:
            rule = json.loads(json.dumps(original, ensure_ascii=False))
            rule_id = rule.get("rule_id")
            if not isinstance(rule_id, str) or not rule_id:
                raise SystemExit(f"{path}: rule_id is required")
            if rule_id in seen_rule_ids:
                raise SystemExit(f"duplicate rule_id: {rule_id}")
            seen_rule_ids.add(rule_id)
            if rule.get("maturity") not in ALLOWED_MATURITY:
                raise SystemExit(f"{rule_id}: invalid maturity")
            if rule.get("maturity") != "experiment_ready":
                raise SystemExit(f"{rule_id}: non-ready rule cannot enter the experiment pack")
            if not isinstance(rule.get("description"), str) or not rule["description"].strip():
                raise SystemExit(f"{rule_id}: description is required")
            if not isinstance(rule.get("profile_all_tags", []), list):
                raise SystemExit(f"{rule_id}: profile_all_tags must be a list")
            if not isinstance(rule.get("profile_config_equals", {}), dict):
                raise SystemExit(f"{rule_id}: profile_config_equals must be an object")
            validate_condition(rule.get("when"), rule_id)

            emissions = rule.get("emit")
            if not isinstance(emissions, list) or not emissions:
                raise SystemExit(f"{rule_id}: emit must be a non-empty list")
            seen_in_rule: set[str] = set()
            for emission in emissions:
                item_id = emission.get("id")
                if item_id not in catalog:
                    raise SystemExit(f"{rule_id}: unknown catalog item {item_id}")
                if item_id in seen_in_rule:
                    raise SystemExit(f"{rule_id}: duplicate emission {item_id}")
                seen_in_rule.add(item_id)
                layer = emission.get("layer")
                if layer not in ALLOWED_LAYERS:
                    raise SystemExit(f"{rule_id}: invalid layer for {item_id}")
                if not isinstance(emission.get("reason"), str) or not emission["reason"].strip():
                    raise SystemExit(f"{rule_id}: emission reason is required for {item_id}")

                # The catalog defines whether an item is repeated execution. Source parts are
                # authored by humans and can accidentally place a routine inside Today/Now.
                # Instead of silently accepting that semantic drift, the build records the
                # correction and makes catalog type authoritative for the assembled pack.
                if "R" in catalog[item_id]["type"].split("/") and layer != "routine":
                    normalizations.append({
                        "rule_id": rule_id,
                        "item_id": item_id,
                        "from_layer": layer,
                        "to_layer": "routine",
                        "reason": "catalog item type includes R"
                    })
                    emission["layer"] = "routine"

                referenced_ids.add(item_id)

            rule["source_part"] = str(path)
            rules.append(rule)

    by_domain = Counter(catalog[item_id]["domain"] for item_id in referenced_ids)
    payload = {
        "schema_version": 2,
        "catalog_item_count": len(catalog),
        "rule_maturity_required": "experiment_ready",
        "layer_policy": "catalog_type_R_forces_routine",
        "source_parts": parts,
        "rule_count": len(rules),
        "referenced_catalog_item_count": len(referenced_ids),
        "unreferenced_catalog_item_ids": sorted(set(catalog) - referenced_ids),
        "routine_layer_normalizations": normalizations,
        "referenced_by_domain": dict(sorted(by_domain.items())),
        "rules": rules,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "parts": len(parts),
        "rules": len(rules),
        "catalog_items": len(catalog),
        "referenced_catalog_items": len(referenced_ids),
        "unreferenced_catalog_items": len(catalog) - len(referenced_ids),
        "routine_layer_normalizations": len(normalizations),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
