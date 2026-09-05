#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

LAYER_RANK = {"now": 4, "today": 3, "review": 2, "routine": 1}
PASS_STATUSES = {"PASS_DIRECT", "PASS_WITH_BOUNDARY"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def get_path(data: dict, path: str, missing: Any = None) -> Any:
    cur: Any = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return missing
        cur = cur[part]
    return cur


def path_present(data: dict, path: str) -> bool:
    marker = object()
    value = get_path(data, path, marker)
    return value is not marker and value is not None


def eval_leaf(state: dict, leaf: dict) -> bool:
    path = leaf["path"]
    op = leaf["op"]
    marker = object()
    value = get_path(state, path, marker)
    if op == "exists":
        return value is not marker and value is not None
    if op == "not_exists":
        return value is marker or value is None
    if op == "truthy":
        return value is not marker and bool(value)
    if op == "falsy":
        return value is not marker and not bool(value)
    if value is marker:
        return False
    target = leaf.get("value")
    if op == "eq":
        return value == target
    if op == "ne":
        return value != target
    if op == "in":
        return value in target
    if op == "not_in":
        return value not in target
    if op == "lt":
        return isinstance(value, (int, float)) and value < target
    if op == "lte":
        return isinstance(value, (int, float)) and value <= target
    if op == "gt":
        return isinstance(value, (int, float)) and value > target
    if op == "gte":
        return isinstance(value, (int, float)) and value >= target
    if op == "contains":
        return isinstance(value, (list, str, dict)) and target in value
    if op == "intersects":
        return isinstance(value, list) and bool(set(value) & set(target))
    raise ValueError(f"unsupported op: {op}")


def eval_condition(state: dict, condition: dict) -> bool:
    if "all" in condition:
        return all(eval_condition(state, x) for x in condition["all"])
    if "any" in condition:
        return any(eval_condition(state, x) for x in condition["any"])
    if "not" in condition:
        return not eval_condition(state, condition["not"])
    return eval_leaf(state, condition)


def profile_capabilities(profile: dict, state: dict) -> set[str]:
    caps = set(profile.get("tags", []))
    config = profile.get("household_config", {})
    for key, value in config.items():
        if value is True:
            caps.add(key)
    runtime = state.get("profile_runtime", {})
    for key, value in runtime.items():
        if value is True:
            caps.add(key)
    return caps


def profile_matches(rule: dict, profile: dict, state: dict) -> tuple[bool, list[str]]:
    caps = profile_capabilities(profile, state)
    missing = [tag for tag in rule.get("profile_all_tags", []) if tag not in caps]
    if missing:
        return False, [f"missing_tag:{x}" for x in missing]
    config = profile.get("household_config", {})
    mismatched = []
    for key, expected in rule.get("profile_config_equals", {}).items():
        if config.get(key) != expected:
            mismatched.append(f"config:{key}")
    return not mismatched, mismatched


def load_health_gate(review_path: Path, boundaries_path: Path) -> tuple[dict, dict]:
    review = json.loads(review_path.read_text(encoding="utf-8"))
    boundaries = json.loads(boundaries_path.read_text(encoding="utf-8"))["items"]
    return {x["id"]: x for x in review["items"]}, boundaries


def derive_candidates(catalog: list[dict], profile: dict, state: dict, rule_pack: dict,
                      health_review: dict, health_boundaries: dict, bundle_map: dict) -> dict:
    by_id = {row["id"]: row for row in catalog}
    emitted: dict[str, dict] = {}
    cards: dict[str, dict] = {}
    suppressed = []
    fired_rules = []
    skipped_rules = []

    for rule in rule_pack["rules"]:
        if rule.get("maturity") != rule_pack.get("rule_maturity_required", "experiment_ready"):
            skipped_rules.append({"rule_id": rule["rule_id"], "reason": "maturity_not_ready"})
            continue
        matches, profile_reasons = profile_matches(rule, profile, state)
        if not matches:
            skipped_rules.append({"rule_id": rule["rule_id"], "reason": ",".join(profile_reasons)})
            continue
        if not eval_condition(state, rule["when"]):
            continue
        fired_rules.append(rule["rule_id"])
        bundle = bundle_map.get(rule["rule_id"], {
            "bundle_id": rule["rule_id"],
            "label": rule.get("description") or rule["rule_id"],
            "close_condition": "該当する責任ループの未完了事項を閉じる"
        })
        card = cards.setdefault(bundle["bundle_id"], {
            "card_id": bundle["bundle_id"],
            "label": bundle["label"],
            "layer": "routine",
            "member_ids": [],
            "rule_ids": [],
            "reasons": [],
            "close_condition": bundle["close_condition"]
        })
        if rule["rule_id"] not in card["rule_ids"]:
            card["rule_ids"].append(rule["rule_id"])

        for emission in rule["emit"]:
            item_id = emission["id"]
            if item_id not in by_id:
                raise ValueError(f"{rule['rule_id']}: unknown catalog item {item_id}")
            meta = by_id[item_id]
            parts = meta["type"].split("/")

            if "S" in parts:
                review = health_review.get(item_id)
                if not review or review["status"] not in PASS_STATUSES:
                    suppressed.append({
                        "id": item_id,
                        "rule_id": rule["rule_id"],
                        "reason": "health_safety_review_blocked",
                        "status": review["status"] if review else "missing_review"
                    })
                    continue
                if review["status"] == "PASS_WITH_BOUNDARY":
                    boundary = health_boundaries.get(item_id)
                    if not boundary:
                        suppressed.append({
                            "id": item_id,
                            "rule_id": rule["rule_id"],
                            "reason": "missing_boundary_rule"
                        })
                        continue
                    missing_paths = [
                        path for path in boundary["required_context_paths"]
                        if not path_present(state, path)
                    ]
                    if missing_paths:
                        suppressed.append({
                            "id": item_id,
                            "rule_id": rule["rule_id"],
                            "reason": "boundary_context_missing",
                            "missing_paths": missing_paths
                        })
                        continue

            candidate = {
                "id": item_id,
                "label": meta["label"],
                "layer": emission["layer"],
                "reason": emission["reason"],
                "rule_ids": [rule["rule_id"]],
                "domain": meta["domain"],
                "type": meta["type"],
                "priority_class": meta["priority_class"],
                "close_condition": meta["close_condition"],
                "source_ids": meta.get("source_ids", []),
                "manual_review_required": meta.get("manual_review_required", False),
                "evidence_rule": meta.get("evidence_rule", {}),
                "metadata_maturity": meta.get("metadata_maturity")
            }
            if item_id not in card["member_ids"]:
                card["member_ids"].append(item_id)
            if emission["reason"] not in card["reasons"]:
                card["reasons"].append(emission["reason"])
            if LAYER_RANK[emission["layer"]] > LAYER_RANK[card["layer"]]:
                card["layer"] = emission["layer"]

            existing = emitted.get(item_id)
            if not existing:
                emitted[item_id] = candidate
            else:
                existing["rule_ids"].append(rule["rule_id"])
                if LAYER_RANK[candidate["layer"]] > LAYER_RANK[existing["layer"]]:
                    existing["layer"] = candidate["layer"]
                    existing["reason"] = candidate["reason"]

    cards = {card_id: card for card_id, card in cards.items() if card["member_ids"]}
    for card in cards.values():
        card["member_ids"].sort()
        card["member_count"] = len(card["member_ids"])

    layers = {layer: [] for layer in LAYER_RANK}
    for item in emitted.values():
        layers[item["layer"]].append(item)
    for layer in layers:
        layers[layer].sort(key=lambda x: (x["domain"], x["id"]))

    card_layers = {layer: [] for layer in LAYER_RANK}
    for card in cards.values():
        card_layers[card["layer"]].append(card)
    for layer in card_layers:
        card_layers[layer].sort(key=lambda x: x["card_id"])

    referenced_ids = {e["id"] for r in rule_pack["rules"] for e in r["emit"]}
    health_ids = {row["id"] for row in catalog if "S" in row["type"].split("/")}
    return {
        "schema_version": 2,
        "date": state.get("date"),
        "profile_id": profile.get("profile_id"),
        "fired_rules": fired_rules,
        "atom_counts": {layer: len(items) for layer, items in layers.items()},
        "card_counts": {layer: len(items) for layer, items in card_layers.items()},
        "total_atoms": sum(len(items) for items in layers.values()),
        "total_cards": sum(len(items) for items in card_layers.values()),
        "layers": layers,
        "cards": card_layers,
        "suppressed": suppressed,
        "coverage": {
            "catalog_items": len(catalog),
            "rule_referenced_items": len(referenced_ids),
            "rule_coverage_ratio": round(len(referenced_ids) / len(catalog), 4),
            "health_safety_catalog_items": len(health_ids),
            "health_safety_rule_referenced_items": len(referenced_ids & health_ids),
            "domains_referenced": sorted({by_id[item_id]["domain"] for item_id in referenced_ids})
        },
        "skipped_rule_count": len(skipped_rules)
    }


def deep_merge(base: dict, patch: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="artifacts/responsibility_catalog_v2.jsonl")
    ap.add_argument("--rules", default="data/activation_rules_core_v2.json")
    ap.add_argument("--profile", default="data/experiment_household_profile_v1.json")
    ap.add_argument("--scenarios", default="data/experiment_raw_state_scenarios_v2.json")
    ap.add_argument("--health-review", default="data/health_safety_review_v2.json")
    ap.add_argument("--health-boundaries", default="data/health_safety_boundaries_v2.json")
    ap.add_argument("--bundles", default="data/surface_bundles_v2.json")
    ap.add_argument("--json-out", default="artifacts/activation_engine_simulation_v2.json")
    ap.add_argument("--md-out", default="artifacts/activation_engine_simulation_v2.md")
    args = ap.parse_args()

    catalog = read_jsonl(Path(args.catalog))
    rule_pack = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    base_profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    review, boundaries = load_health_gate(Path(args.health_review), Path(args.health_boundaries))
    bundle_map = json.loads(Path(args.bundles).read_text(encoding="utf-8"))["rules"]

    if not base_profile.get("synthetic"):
        raise SystemExit("experiment profile must be explicitly synthetic")
    if any("activations" in scenario for scenario in scenarios["scenarios"]):
        raise SystemExit("v2 scenarios must contain raw state only; responsibility activations are forbidden")

    reports = []
    for scenario in scenarios["scenarios"]:
        profile = deep_merge(base_profile, scenario.get("profile_overrides", {}))
        state = scenario["state"]
        reports.append({
            "scenario_id": scenario["id"],
            "title": scenario["title"],
            "synthetic": True,
            "result": derive_candidates(catalog, profile, state, rule_pack, review, boundaries, bundle_map)
        })

    payload = {"schema_version": 2, "synthetic": True, "reports": reports}
    out_path = Path(args.json_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# ACTIVATION ENGINE SIMULATION v2",
        "",
        "責任IDを入力へ直接列挙せず、架空の家庭プロフィールとraw stateから候補を生成した結果。",
        "",
        "| シナリオ | 今見るカード | 今日カード | ルーティン群 | レビューカード | atomic責任 | 抑制 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for report in reports:
        result = report["result"]
        c = result["card_counts"]
        lines.append(
            f"| {report['title']} | {c['now']} | {c['today']} | {c['routine']} | {c['review']} | {result['total_atoms']} | {len(result['suppressed'])} |"
        )
    lines.extend(["", "## Rule coverage", ""])
    coverage = reports[0]["result"]["coverage"] if reports else {}
    lines.append(f"- Effective catalog: {coverage.get('catalog_items', 0)}")
    lines.append(f"- Rule-referenced items: {coverage.get('rule_referenced_items', 0)}")
    lines.append(f"- Rule coverage ratio: {coverage.get('rule_coverage_ratio', 0):.2%}")
    lines.append(f"- Health/safety referenced: {coverage.get('health_safety_rule_referenced_items', 0)} / {coverage.get('health_safety_catalog_items', 0)}")
    lines.append("")
    for report in reports:
        lines.append(f"## {report['title']}")
        lines.append("")
        result = report["result"]
        for layer in ("now", "today", "routine", "review"):
            lines.append(f"### {layer} cards — {result['card_counts'][layer]}")
            lines.append("")
            for card in result["cards"][layer]:
                lines.append(f"- `{card['card_id']}` {card['label']} — {card['member_count']} atomic responsibilities")
            if not result["cards"][layer]:
                lines.append("- なし")
            lines.append("")
        if result["suppressed"]:
            lines.append("### suppressed")
            lines.append("")
            for item in result["suppressed"]:
                lines.append(f"- `{item['id']}` — {item['reason']}")
            lines.append("")
    Path(args.md_out).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        r["scenario_id"]: {
            **{f"cards_{k}": v for k, v in r["result"]["card_counts"].items()},
            "atoms": r["result"]["total_atoms"],
            "suppressed": len(r["result"]["suppressed"])
        } for r in reports
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
