#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_LAYERS = {"now", "today", "routine", "review"}
ALLOWED_OPS = {"exists", "not_exists", "truthy", "falsy", "eq", "ne", "in", "not_in", "lt", "lte", "gt", "gte", "contains", "intersects"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_condition(node: dict, rule_id: str) -> None:
    keys = set(node)
    compound = keys & {"all", "any", "not"}
    if compound:
        if len(compound) != 1 or len(keys) != 1:
            raise ValueError(f"{rule_id}: invalid compound condition {node}")
        key = next(iter(compound))
        if key == "not":
            if not isinstance(node[key], dict):
                raise ValueError(f"{rule_id}: not condition must contain an object")
            validate_condition(node[key], rule_id)
            return
        children = node[key]
        if not isinstance(children, list) or not children:
            raise ValueError(f"{rule_id}: {key} condition must contain a non-empty list")
        for child in children:
            if not isinstance(child, dict):
                raise ValueError(f"{rule_id}: condition child must be an object")
            validate_condition(child, rule_id)
        return

    if "path" not in node or "op" not in node:
        raise ValueError(f"{rule_id}: leaf condition requires path and op")
    if not isinstance(node["path"], str) or not node["path"].strip() or " " in node["path"]:
        raise ValueError(f"{rule_id}: invalid condition path")
    if node["op"] not in ALLOWED_OPS:
        raise ValueError(f"{rule_id}: unsupported condition op {node['op']}")
    if node["op"] not in {"exists", "not_exists", "truthy", "falsy"} and "value" not in node:
        raise ValueError(f"{rule_id}: op {node['op']} requires value")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts-dir", default="data/activation_rules_v2")
    ap.add_argument("--catalog", default="artifacts/responsibility_catalog_v2.jsonl")
    ap.add_argument("--out", default="artifacts/activation_rules_core_v2.json")
    args = ap.parse_args()

    part_paths = sorted(Path(args.parts_dir).glob("*.json"))
    if not part_paths:
        raise SystemExit("no activation rule part files found")

    catalog = read_jsonl(Path(args.catalog))
    catalog_ids = {row["id"] for row in catalog}
    rules: list[dict] = []
    rule_ids: set[str] = set()
    emitted_ids: set[str] = set()
    parts = []

    for path in part_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 2:
            raise SystemExit(f"{path}: schema_version must be 2")
        part_name = payload.get("part")
        if not isinstance(part_name, str) or not part_name:
            raise SystemExit(f"{path}: part is required")
        parts.append({"part": part_name, "path": str(path), "rule_count": len(payload.get("rules", []))})
        for rule in payload.get("rules", []):
            rule_id = rule.get("rule_id")
            if not isinstance(rule_id, str) or not rule_id:
                raise SystemExit(f"{path}: rule_id is required")
            if rule_id in rule_ids:
                raise SystemExit(f"duplicate rule_id: {rule_id}")
            rule_ids.add(rule_id)
            if rule.get("maturity") not in {"experiment_ready", "draft", "blocked"}:
                raise SystemExit(f"{rule_id}: invalid maturity")
            if not isinstance(rule.get("profile_all_tags", []), list):
                raise SystemExit(f"{rule_id}: profile_all_tags must be a list")
            if not isinstance(rule.get("profile_config_equals", {}), dict):
                raise SystemExit(f"{rule_id}: profile_config_equals must be an object")
            validate_condition(rule.get("when", {}), rule_id)
            emissions = rule.get("emit")
            if not isinstance(emissions, list) or not emissions:
                raise SystemExit(f"{rule_id}: emit must be a non-empty list")
            seen_in_rule = set()
            for emission in emissions:
                item_id = emission.get("id")
                if item_id not in catalog_ids:
                    raise SystemExit(f"{rule_id}: unknown catalog item {item_id}")
                if item_id in seen_in_rule:
                    raise SystemExit(f"{rule_id}: duplicate emission {item_id}")
                seen_in_rule.add(item_id)
                emitted_ids.add(item_id)
                if emission.get("layer") not in ALLOWED_LAYERS:
                    raise SystemExit(f"{rule_id}: invalid layer for {item_id}")
                if not isinstance(emission.get("reason"), str) or not emission["reason"].strip():
                    raise SystemExit(f"{rule_id}: emission reason is required for {item_id}")
            rules.append(rule)

    payload = {
        "schema_version": 2,
        "rule_maturity_required": "experiment_ready",
        "source_parts": parts,
        "rule_count": len(rules),
        "referenced_catalog_item_count": len(emitted_ids),
        "rules": rules,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "parts": len(parts),
        "rules": len(rules),
        "catalog_items": len(catalog_ids),
        "referenced_catalog_items": len(emitted_ids),
        "unreferenced_catalog_items": len(catalog_ids - emitted_ids),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
