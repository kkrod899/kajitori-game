#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="artifacts/activation_rules_core_v2.json")
    ap.add_argument("--patterns", default="data/surface_bundle_patterns_v2.json")
    ap.add_argument("--out", default="artifacts/surface_bundles_v2.json")
    args = ap.parse_args()

    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))["rules"]
    pattern_payload = json.loads(Path(args.patterns).read_text(encoding="utf-8"))
    patterns = pattern_payload["patterns"]

    seen_prefixes = set()
    for pattern in patterns:
        prefix = pattern.get("prefix")
        if not isinstance(prefix, str) or not prefix:
            raise SystemExit("bundle pattern requires a non-empty prefix")
        if prefix in seen_prefixes:
            raise SystemExit(f"duplicate bundle prefix: {prefix}")
        seen_prefixes.add(prefix)
        for field in ("bundle_id", "label", "close_condition"):
            if not isinstance(pattern.get(field), str) or not pattern[field].strip():
                raise SystemExit(f"{prefix}: {field} is required")

    mapping = {}
    unmatched = []
    for rule in rules:
        rule_id = rule["rule_id"]
        matches = [p for p in patterns if rule_id.startswith(p["prefix"])]
        if not matches:
            unmatched.append(rule_id)
            mapping[rule_id] = {
                "bundle_id": rule_id,
                "label": rule.get("description") or rule_id,
                "close_condition": "該当する責任ループの未完了事項を閉じる",
                "matched_prefix": None
            }
            continue
        pattern = max(matches, key=lambda p: len(p["prefix"]))
        mapping[rule_id] = {
            "bundle_id": pattern["bundle_id"],
            "label": pattern["label"],
            "close_condition": pattern["close_condition"],
            "matched_prefix": pattern["prefix"]
        }

    payload = {
        "schema_version": 2,
        "rule_count": len(rules),
        "mapped_rule_count": len(mapping),
        "unmatched_rule_ids": unmatched,
        "rules": mapping
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "rules": len(rules),
        "unique_bundles": len({x["bundle_id"] for x in mapping.values()}),
        "unmatched": len(unmatched)
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
