#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT_FALLBACKS = {
    "routine": ("routine.misc", "日常の反復ケア", "その時間帯に必要な反復実行と後片付けを閉じる"),
    "infant": ("infant.misc", "赤ちゃんまわりの確認", "現在状態を確認し、必要な準備・補充・相談の次アクションを確定する"),
    "health": ("health.misc", "健康・医療まわり", "観察事実と公式・医療機関情報に基づき、必要な次アクションを確定する"),
    "daycare": ("daycare.misc", "園まわりの確認", "連絡・準備・提出・引継ぎの未完了を閉じる"),
    "food": ("food.misc", "食事まわり", "方針・在庫・買い物・保存の未完了を閉じる"),
    "kitchen": ("kitchen.misc", "キッチンまわり", "次に安全・衛生的に使える状態まで未完了を閉じる"),
    "laundry": ("laundry.misc", "洗濯まわり", "洗う・乾かす・戻すまでの止まっている工程を閉じる"),
    "cleaning": ("cleaning.misc", "掃除・片付け", "該当場所を安全・衛生的に使える状態へ戻す"),
    "supplies": ("supplies.misc", "日用品の補充", "不足品を特定し、購入・収納または共有リスト反映まで確定する"),
    "waste": ("waste.misc", "ごみ・回収", "回収・分類・搬出・保管場所の未完了を閉じる"),
    "planning": ("planning.misc", "予定・移動", "日時・担当・移動・持ち物の未確定を閉じる"),
    "admin": ("admin.misc", "書類・支払", "期限と必要情報を確認し、提出・更新・保管の未完了を閉じる"),
    "family": ("family.misc", "家族の引継ぎ", "状態・担当・休息・バックアップの未確定を共有して閉じる"),
    "older": ("older.misc", "上の子まわり", "体調・準備・用品・個別時間の必要対応を確定する"),
    "growth": ("growth.misc", "成長・季節の見直し", "現在の適合を確認し、対応不要または期限付き更新行動を確定する"),
    "play": ("play.misc", "遊び・親子時間", "遊び場所・玩具・個別時間の必要対応を確定する"),
    "safety": ("safety.misc", "安全状態の確認", "観察された危険要因を除去・隔離・回避し、現在状態を記録する"),
    "emergency": ("emergency.misc", "災害・緊急時の備え", "該当する避難・備蓄・連絡・設備確認を行い、不足を具体的行動へする"),
    "home": ("home.misc", "住まい・設備", "異常または点検条件を修理・交換・清掃・経過確認へつなぐ"),
}


def load_patterns(paths: list[Path]) -> list[dict]:
    patterns: list[dict] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 2:
            raise SystemExit(f"{path}: schema_version must be 2")
        entries = payload.get("patterns")
        if not isinstance(entries, list):
            raise SystemExit(f"{path}: patterns must be a list")
        for entry in entries:
            copy = dict(entry)
            copy["source_file"] = str(path)
            patterns.append(copy)
    return patterns


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="artifacts/activation_rules_core_v2.json")
    ap.add_argument("--patterns", default="data/surface_bundle_patterns_v2.json")
    ap.add_argument("--additional-patterns", default="data/surface_bundle_patterns_v2r2_additions.json")
    ap.add_argument("--out", default="artifacts/surface_bundles_v2.json")
    args = ap.parse_args()

    rule_payload = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    rules = rule_payload["rules"]
    patterns = load_patterns([Path(args.patterns), Path(args.additional_patterns)])

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
    root_fallbacks = []
    unmatched = []
    for rule in rules:
        rule_id = rule["rule_id"]
        matches = [p for p in patterns if rule_id.startswith(p["prefix"])]
        if matches:
            pattern = max(matches, key=lambda p: len(p["prefix"]))
            mapping[rule_id] = {
                "bundle_id": pattern["bundle_id"],
                "label": pattern["label"],
                "close_condition": pattern["close_condition"],
                "matched_prefix": pattern["prefix"],
                "mapping_kind": "explicit_pattern",
                "source_file": pattern["source_file"],
            }
            continue

        root = rule_id.split(".", 1)[0]
        if root in ROOT_FALLBACKS:
            bundle_id, label, close_condition = ROOT_FALLBACKS[root]
            mapping[rule_id] = {
                "bundle_id": bundle_id,
                "label": label,
                "close_condition": close_condition,
                "matched_prefix": root + ".",
                "mapping_kind": "root_fallback",
                "source_file": "builtin_root_fallback",
            }
            root_fallbacks.append(rule_id)
        else:
            unmatched.append(rule_id)

    if unmatched:
        raise SystemExit(f"unmatched rule roots: {unmatched}")

    payload = {
        "schema_version": 2,
        "rule_count": len(rules),
        "mapped_rule_count": len(mapping),
        "unmatched_rule_ids": unmatched,
        "root_fallback_rule_ids": root_fallbacks,
        "rules": mapping,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    kind_counts = Counter(x["mapping_kind"] for x in mapping.values())
    print(json.dumps({
        "rules": len(rules),
        "unique_bundles": len({x["bundle_id"] for x in mapping.values()}),
        "mapping_kinds": dict(kind_counts),
        "root_fallbacks": len(root_fallbacks),
        "unmatched": len(unmatched),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
