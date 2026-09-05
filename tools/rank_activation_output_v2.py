#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

LAYER_RANK = {"now": 0, "today": 1, "routine": 2, "review": 3}
PRIORITY_RANK = {
    "safety_health_deadline": 0,
    "safety_health": 1,
    "deadline": 2,
    "capacity": 3,
    "high": 4,
    "essential_routine": 5,
    "maintenance": 6,
}
ATTENTION_LABEL = {
    0: "健康・安全または重大期限",
    1: "健康・安全の状態変化",
    2: "期限が近い",
    3: "家庭の余力・担当を再調整",
    4: "今日の高優先判断",
    5: "必要な反復ケア",
    6: "保守・定期レビュー",
}


def atomic_key(item: dict) -> tuple:
    return (
        LAYER_RANK[item["layer"]],
        PRIORITY_RANK.get(item.get("priority_class"), 99),
        item.get("domain", ""),
        item["id"],
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="artifacts/activation_engine_v2.json")
    ap.add_argument("--out", default="artifacts/activation_engine_v2_ranked.json")
    args = ap.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    for report in payload["reports"]:
        atomic_by_id = {item["id"]: item for item in report["atomic_candidates"]}
        for item in report["atomic_candidates"]:
            priority_rank = PRIORITY_RANK.get(item.get("priority_class"), 99)
            item["attention_class"] = item.get("priority_class", "unknown")
            item["attention_label"] = ATTENTION_LABEL.get(priority_rank, "その他")
            item["attention_order_key"] = [LAYER_RANK[item["layer"]], priority_rank]
        report["atomic_candidates"].sort(key=atomic_key)

        for card in report["cards"]:
            members = [atomic_by_id[item_id] for item_id in card["atomic_ids"]]
            best = min(members, key=atomic_key)
            card["attention_class"] = best["attention_class"]
            card["attention_label"] = best["attention_label"]
            card["attention_order_key"] = best["attention_order_key"]
        report["cards"].sort(key=lambda card: (tuple(card["attention_order_key"]), card["label"], card["card_id"]))

    payload["attention_ordering_version"] = "lexicographic-v1"
    payload["attention_policy"] = {
        "no_candidate_truncation": True,
        "no_fixed_target_count": True,
        "order": [
            "layer: now before today before routine before review",
            "priority: safety/health deadline, safety/health, deadline, capacity, high, routine, maintenance",
            "stable domain/id tie-break only"
        ]
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "reports": len(payload["reports"]),
        "attention_ordering_version": payload["attention_ordering_version"],
        "candidates_preserved": sum(r["atomic_total"] for r in payload["reports"]),
        "cards_preserved": sum(r["card_total"] for r in payload["reports"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
