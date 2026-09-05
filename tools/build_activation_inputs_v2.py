#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_rule_parts(directory: Path) -> list[dict]:
    files = sorted(directory.glob("*.json"))
    if not files:
        raise SystemExit(f"no activation rule parts in {directory}")
    merged: list[dict] = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rules = payload.get("rules")
        if not isinstance(rules, list):
            raise SystemExit(f"activation rule part must contain a rules array: {path}")
        merged.extend(rules)
    ids = [item.get("rule_id") for item in merged]
    if any(not item for item in ids):
        raise SystemExit("activation rule without rule_id")
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate rule IDs across activation parts")
    return merged


def load_bundle_parts(directory: Path) -> dict[str, dict]:
    files = sorted(directory.glob("*.json"))
    if not files:
        raise SystemExit(f"no surface bundle parts in {directory}")
    merged: dict[str, dict] = {}
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        bundles = payload.get("rules")
        if not isinstance(bundles, dict):
            raise SystemExit(f"surface bundle part must contain a rules object: {path}")
        overlap = set(merged) & set(bundles)
        if overlap:
            raise SystemExit(f"duplicate bundle rule IDs: {sorted(overlap)}")
        merged.update(bundles)
    return merged


def load_scenario_parts(directory: Path) -> list[dict]:
    files = sorted(directory.glob("*.json"))
    if not files:
        raise SystemExit(f"no raw-state scenario parts in {directory}")
    scenarios: list[dict] = []
    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not payload.get("id"):
            raise SystemExit(f"scenario part must be one scenario object with id: {path}")
        scenarios.append(payload)
    scenario_ids = [item["id"] for item in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        raise SystemExit("duplicate scenario IDs")
    if any("activations" in item for item in scenarios):
        raise SystemExit("v2 scenarios must use raw state, not activations")
    return scenarios


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules-dir", default="data/activation_rules_v2")
    ap.add_argument("--bundles-dir", default="data/surface_bundles_v2")
    ap.add_argument("--scenarios-dir", default="data/experiment_raw_state_scenarios_v2")
    ap.add_argument("--rules-out", default="artifacts/activation_rules_core_v2.json")
    ap.add_argument("--bundles-out", default="artifacts/surface_bundles_v2.json")
    ap.add_argument("--scenarios-out", default="artifacts/experiment_raw_state_scenarios_v2.json")
    args = ap.parse_args()

    rules = load_rule_parts(Path(args.rules_dir))
    bundles = load_bundle_parts(Path(args.bundles_dir))
    scenarios = load_scenario_parts(Path(args.scenarios_dir))

    rule_ids = {item["rule_id"] for item in rules}
    if set(bundles) != rule_ids:
        raise SystemExit(
            "rule/bundle ID mismatch "
            f"missing_bundles={sorted(rule_ids - set(bundles))} "
            f"extra_bundles={sorted(set(bundles) - rule_ids)}"
        )

    outputs = [
        (
            Path(args.rules_out),
            {
                "schema_version": 2,
                "description": "raw-state experiment-ready activation rule pack",
                "layer_precedence": ["now", "today", "review", "routine"],
                "rule_maturity_required": "experiment_ready",
                "rules": rules,
            },
        ),
        (
            Path(args.bundles_out),
            {
                "schema_version": 2,
                "description": "complete-loop user-facing bundles keyed by activation rule",
                "rules": bundles,
            },
        ),
        (
            Path(args.scenarios_out),
            {
                "schema_version": 2,
                "description": "synthetic raw-state scenarios; no responsibility IDs as inputs",
                "scenarios": scenarios,
            },
        ),
    ]
    for path, payload in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"rules": len(rules), "bundles": len(bundles), "scenarios": len(scenarios)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
