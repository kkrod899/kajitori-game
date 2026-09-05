#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

LAYERS = ["now", "today", "routine", "review"]
LAYER_RANK = {"now": 0, "today": 1, "routine": 2, "review": 3}
LAYER_JA = {"now": "今見る", "today": "今日の候補", "routine": "ルーティン", "review": "レビュー"}
PASS_STATUSES = {"PASS_DIRECT", "PASS_WITH_BOUNDARY"}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def get_path(data: dict, path: str) -> tuple[bool, object]:
    current: object = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def eval_leaf(node: dict, state: dict) -> bool:
    found, actual = get_path(state, node["path"])
    op = node["op"]
    if op == "exists":
        return found and actual is not None
    if op == "not_exists":
        return not found or actual is None
    # Missing values are unknown, never implicitly false/safe/complete.
    if not found:
        return False
    if op == "truthy":
        return bool(actual)
    if op == "falsy":
        return not bool(actual)
    expected = node.get("value")
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if op == "lt":
        return actual < expected
    if op == "lte":
        return actual <= expected
    if op == "gt":
        return actual > expected
    if op == "gte":
        return actual >= expected
    if op == "contains":
        return expected in actual
    if op == "intersects":
        return bool(set(actual) & set(expected))
    raise ValueError(f"unsupported condition op: {op}")


def eval_condition(node: dict, state: dict) -> bool:
    if "all" in node:
        return all(eval_condition(child, state) for child in node["all"])
    if "any" in node:
        return any(eval_condition(child, state) for child in node["any"])
    if "not" in node:
        return not eval_condition(node["not"], state)
    return eval_leaf(node, state)


def profile_capabilities(profile: dict) -> set[str]:
    caps = set(profile.get("tags", []))
    for key, value in profile.get("household_config", {}).items():
        if value is True:
            caps.add(key)
    return caps


def profile_gate(rule: dict, profile: dict, state: dict) -> tuple[bool, list[str]]:
    caps = profile_capabilities(profile)
    missing_tags = [tag for tag in rule.get("profile_all_tags", []) if tag not in caps]
    if missing_tags:
        return False, [f"missing_tag:{tag}" for tag in missing_tags]

    config = profile.get("household_config", {})
    runtime = state.get("profile_runtime", {}) if isinstance(state.get("profile_runtime"), dict) else {}
    mismatches = []
    for key, expected in rule.get("profile_config_equals", {}).items():
        if key in runtime:
            actual = runtime[key]
        elif key in config:
            actual = config[key]
        else:
            mismatches.append(f"missing_config:{key}")
            continue
        if actual != expected:
            mismatches.append(f"config_mismatch:{key}")
    return not mismatches, mismatches


def load_review(review_path: Path, boundary_path: Path) -> tuple[dict, dict]:
    review = {row["id"]: row for row in json.loads(review_path.read_text(encoding="utf-8"))["items"]}
    boundaries = {row["id"]: row for row in json.loads(boundary_path.read_text(encoding="utf-8"))["items"]}
    return review, boundaries


def health_safety_gate(item: dict, state: dict, review: dict, boundaries: dict) -> tuple[bool, dict | None]:
    if "S" not in item["type"].split("/"):
        return True, None
    item_id = item["id"]
    gate = review.get(item_id)
    if gate is None:
        return False, {"item_id": item_id, "reason": "missing_manual_review"}
    status = gate.get("status")
    if status not in PASS_STATUSES:
        return False, {"item_id": item_id, "reason": f"review_status:{status}"}
    missing_sources = sorted(set(gate.get("required_source_ids", [])) - set(item.get("source_ids", [])))
    if missing_sources:
        return False, {"item_id": item_id, "reason": "missing_required_sources", "missing_source_ids": missing_sources}
    if status == "PASS_WITH_BOUNDARY":
        boundary = boundaries.get(item_id)
        if boundary is None:
            return False, {"item_id": item_id, "reason": "missing_boundary_definition"}
        missing_paths = []
        for path in boundary.get("required_context_paths", []):
            found, value = get_path(state, path)
            if not found or value is None:
                missing_paths.append(path)
        if missing_paths:
            return False, {"item_id": item_id, "reason": "missing_boundary_input", "missing_boundary_paths": missing_paths}
    return True, None


def derive(catalog_rows: list[dict], rules: list[dict], profile: dict, scenario: dict,
           review: dict, boundaries: dict, bundles: dict) -> dict:
    if "activations" in scenario or "activations" in scenario.get("state", {}):
        raise ValueError(f"{scenario.get('id')}: direct responsibility activation is forbidden in v2")
    state = scenario["state"]
    catalog = {row["id"]: row for row in catalog_rows}

    candidates: dict[str, dict] = {}
    suppressed: list[dict] = []
    evaluation = {"rule_count": len(rules), "profile_blocked": 0, "condition_false": 0, "fired": 0}

    for rule in rules:
        allowed, profile_reasons = profile_gate(rule, profile, state)
        if not allowed:
            evaluation["profile_blocked"] += 1
            continue
        if not eval_condition(rule["when"], state):
            evaluation["condition_false"] += 1
            continue
        evaluation["fired"] += 1
        bundle = bundles[rule["rule_id"]]

        for emission in rule["emit"]:
            item = catalog[emission["id"]]
            allowed_item, suppression = health_safety_gate(item, state, review, boundaries)
            if not allowed_item:
                suppression.update({"rule_id": rule["rule_id"], "layer": emission["layer"]})
                suppressed.append(suppression)
                continue

            item_id = item["id"]
            entry = candidates.get(item_id)
            contribution = {
                "rule_id": rule["rule_id"],
                "layer": emission["layer"],
                "reason": emission["reason"],
                "bundle_id": bundle["bundle_id"],
                "bundle_label": bundle["label"],
                "bundle_close_condition": bundle["close_condition"],
            }
            if entry is None:
                entry = {
                    "id": item_id,
                    "label": item["label"],
                    "type": item["type"],
                    "domain": item["domain"],
                    "priority_class": item["priority_class"],
                    "source_ids": item.get("source_ids", []),
                    "manual_review_required": item.get("manual_review_required", False),
                    "layer": emission["layer"],
                    "primary_rule_id": rule["rule_id"],
                    "primary_bundle_id": bundle["bundle_id"],
                    "primary_bundle_label": bundle["label"],
                    "primary_bundle_close_condition": bundle["close_condition"],
                    "contributions": [contribution],
                }
                candidates[item_id] = entry
            else:
                entry["contributions"].append(contribution)
                if LAYER_RANK[emission["layer"]] < LAYER_RANK[entry["layer"]]:
                    entry["layer"] = emission["layer"]
                    entry["primary_rule_id"] = rule["rule_id"]
                    entry["primary_bundle_id"] = bundle["bundle_id"]
                    entry["primary_bundle_label"] = bundle["label"]
                    entry["primary_bundle_close_condition"] = bundle["close_condition"]

    atomic = sorted(candidates.values(), key=lambda x: (LAYER_RANK[x["layer"]], x["domain"], x["id"]))

    grouped = defaultdict(list)
    for item in atomic:
        grouped[(item["layer"], item["primary_bundle_id"])].append(item)

    cards = []
    for (layer, bundle_id), items in grouped.items():
        cards.append({
            "card_id": f"{layer}:{bundle_id}",
            "layer": layer,
            "bundle_id": bundle_id,
            "label": items[0]["primary_bundle_label"],
            "close_condition": items[0]["primary_bundle_close_condition"],
            "atomic_ids": [item["id"] for item in items],
            "atomic_labels": [item["label"] for item in items],
            "domains": sorted({item["domain"] for item in items}),
            "contains_health_safety": any(item["manual_review_required"] for item in items),
            "reasons": sorted({c["reason"] for item in items for c in item["contributions"]}),
        })
    cards.sort(key=lambda x: (LAYER_RANK[x["layer"]], x["label"], x["card_id"]))

    counts = {layer: sum(1 for item in atomic if item["layer"] == layer) for layer in LAYERS}
    card_counts = {layer: sum(1 for card in cards if card["layer"] == layer) for layer in LAYERS}
    return {
        "id": scenario["id"],
        "title": scenario["title"],
        "synthetic": True,
        "counts": counts,
        "card_counts": card_counts,
        "atomic_total": len(atomic),
        "card_total": len(cards),
        "rule_evaluation": evaluation,
        "atomic_candidates": atomic,
        "cards": cards,
        "suppressed_health_safety": suppressed,
    }


def to_markdown(reports: list[dict]) -> str:
    lines = [
        "# RAW-STATE ACTIVATION ENGINE v2 r2",
        "",
        "このレポートは架空状態だけを入力にした決定論的シミュレーション。責任IDを直接指定していない。",
        "",
        "`Atomic`は裏側の責任単位、`Cards`は同じ判断・完結ループへ束ねた表示単位。件数は目標ではなく、その状態で表示根拠が成立した量。",
        "",
        "| シナリオ | Atomic 今 | Atomic 今日 | Atomic ルーティン | Atomic レビュー | Cards 今 | Cards 今日 | Cards ルーティン | Cards レビュー |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for report in reports:
        c, cc = report["counts"], report["card_counts"]
        lines.append(f"| {report['title']} | {c['now']} | {c['today']} | {c['routine']} | {c['review']} | {cc['now']} | {cc['today']} | {cc['routine']} | {cc['review']} |")
    lines.append("")
    for report in reports:
        lines.extend([f"## {report['title']}", ""])
        for layer in LAYERS:
            cards = [card for card in report["cards"] if card["layer"] == layer]
            lines.extend([f"### {LAYER_JA[layer]} — {len(cards)}カード / {report['counts'][layer]}責任", ""])
            if not cards:
                lines.extend(["該当なし。", ""])
                continue
            for card in cards:
                lines.append(f"- **{card['label']}** — {', '.join(card['atomic_labels'])}")
                lines.append(f"  - 終了条件: {card['close_condition']}")
            lines.append("")
        if report["suppressed_health_safety"]:
            lines.append("### 健康・安全ゲートで抑制")
            lines.append("")
            for item in report["suppressed_health_safety"]:
                lines.append(f"- `{item['item_id']}`: {item['reason']}")
            lines.append("")
    lines.extend([
        "## この結果が証明しないこと",
        "",
        "- 実生活で必要な責任を十分に拾えること",
        "- 表示カードの量・文言・タイミングが人間にとって適切であること",
        "- 入力負担が継続可能であること",
        "- パートナーからの指示依存や完結漏れが減ること",
        "",
        "これらは7日shadow baselineで、atomicな見落としとcard単位のノイズを分けて測る。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="artifacts/responsibility_catalog_v2.jsonl")
    ap.add_argument("--rules", default="artifacts/activation_rules_core_v2.json")
    ap.add_argument("--profile", default="data/experiment_household_profile_v1.json")
    ap.add_argument("--scenarios", default="data/experiment_raw_state_scenarios_v2.json")
    ap.add_argument("--review", default="data/health_safety_review_v2.json")
    ap.add_argument("--boundaries", default="data/health_safety_boundaries_v2.json")
    ap.add_argument("--bundles", default="artifacts/surface_bundles_v2.json")
    ap.add_argument("--json-out", default="artifacts/activation_engine_v2.json")
    ap.add_argument("--md-out", default="artifacts/activation_engine_v2.md")
    args = ap.parse_args()

    catalog = read_jsonl(Path(args.catalog))
    rule_payload = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    rules = rule_payload["rules"]
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    if not profile.get("synthetic"):
        raise SystemExit("experiment profile must be explicitly synthetic")
    review, boundaries = load_review(Path(args.review), Path(args.boundaries))
    bundles = json.loads(Path(args.bundles).read_text(encoding="utf-8"))["rules"]

    reports = [derive(catalog, rules, profile, scenario, review, boundaries, bundles) for scenario in scenarios["scenarios"]]
    payload = {
        "schema_version": 2,
        "engine_version": "v2-r2",
        "synthetic": True,
        "fixed_target_count": None,
        "reports": reports,
    }
    json_out = Path(args.json_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.md_out).write_text(to_markdown(reports), encoding="utf-8")

    print(json.dumps({report["id"]: {"atomic": report["counts"], "cards": report["card_counts"], "suppressed": len(report["suppressed_health_safety"])} for report in reports}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
