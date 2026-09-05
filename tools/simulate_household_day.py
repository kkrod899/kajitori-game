#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

LAYERS = ["now", "today", "routine", "review"]
LAYER_JA = {"now":"今見る", "today":"今日の候補", "routine":"ルーティン", "review":"レビュー"}


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_applicable(meta, profile):
    tags = set(profile.get("tags", []))
    missing = [tag for tag in meta.get("applicability", []) if tag not in tags]
    return not missing, missing


def validate_config(meta, profile):
    if not meta.get("requires_household_config"):
        return True, []
    config = profile.get("household_config", {})
    missing = [key for key in meta.get("household_config_fields", []) if key not in config]
    return not missing, missing


def decide_layer(meta, signal):
    trigger = meta["trigger_type"]
    priority = meta["priority_class"]

    if trigger == "routine" or signal.get("routine_expected"):
        return "routine", "反復実行として別ストリームに分離"

    if signal.get("urgent"):
        return "now", "シナリオ上、今の計画を崩しうる状態変化"

    if signal.get("hazard_present") or signal.get("health_changed"):
        return "now", "健康・安全の状態変化がある"

    if trigger == "schedule":
        due_hours = signal.get("due_hours")
        if isinstance(due_hours, (int, float)) and due_hours <= 24:
            return "now", f"期限まで{due_hours:g}時間"
        if signal.get("due_today") or signal.get("transition_due"):
            return "today", "今日中に期限・引継ぎ条件を閉じる"
        if signal.get("review_due"):
            return "review", "日程・期限設定の定期レビュー"

    if trigger == "inventory":
        if signal.get("critical"):
            return "now", "在庫が次の通常補充機会まで持たない"
        if signal.get("threshold_breached"):
            return "today", "在庫が家庭設定の補充判断ライン以下"
        if signal.get("review_due"):
            return "review", "在庫・期限の定期レビュー"

    if trigger in {"safety", "health_state"}:
        if signal.get("context_changed") or signal.get("state_changed"):
            return "now", "健康・安全に関係する文脈または状態が変化"
        if signal.get("review_due"):
            return "review", "健康・安全項目の定期レビュー"

    if trigger == "lifecycle":
        if signal.get("context_changed"):
            if priority.startswith("safety_health"):
                return "now", "安全に関わる成長・季節条件が変化"
            return "today", "成長・季節条件が変化"
        if signal.get("review_due"):
            return "review", "成長・サイズ・季節の定期レビュー"

    if signal.get("transition_due"):
        return "today", "担当・引継ぎを今日中に閉じる"

    if signal.get("action_required") or signal.get("state_changed") or signal.get("state_unknown") or signal.get("due_today"):
        return "today", "今日の家庭状態から確認・判断・実行が必要"

    if signal.get("review_due"):
        return "review", "定期レビューが期限到来"

    return None, "表示条件なし"


def simulate(metadata, profile, scenarios):
    by_id = {row["id"]: row for row in metadata}
    reports = []
    for scenario in scenarios["scenarios"]:
        seen = set()
        buckets = {k: [] for k in LAYERS}
        for act in scenario.get("activations", []):
            item_id = act["id"]
            if item_id in seen:
                raise ValueError(f"{scenario['id']}: duplicate activation {item_id}")
            seen.add(item_id)
            if item_id not in by_id:
                raise ValueError(f"{scenario['id']}: unknown responsibility {item_id}")
            meta = by_id[item_id]

            applicable, missing_tags = is_applicable(meta, profile)
            if not applicable:
                raise ValueError(f"{scenario['id']}: {item_id} not applicable; missing tags={missing_tags}")

            config_ok, missing_config = validate_config(meta, profile)
            if not config_ok:
                raise ValueError(f"{scenario['id']}: {item_id} missing household config={missing_config}")

            if meta.get("manual_review_required") and not meta.get("source_ids"):
                raise ValueError(f"{scenario['id']}: safety/health item {item_id} lacks official source")

            signal = act.get("signal", {})
            layer, reason = decide_layer(meta, signal)
            if layer is None:
                raise ValueError(f"{scenario['id']}: activation {item_id} produced no surface layer")

            buckets[layer].append({
                "id": item_id,
                "label": meta["label"],
                "domain": meta["domain"],
                "trigger_type": meta["trigger_type"],
                "priority_class": meta["priority_class"],
                "reason": reason,
                "scenario_note": act.get("note", ""),
                "source_ids": meta.get("source_ids", []),
                "manual_review_required": meta.get("manual_review_required", False)
            })

        reports.append({
            "id": scenario["id"],
            "title": scenario["title"],
            "day_type": scenario.get("day_type"),
            "context_tags": scenario.get("context_tags", []),
            "counts": {layer: len(buckets[layer]) for layer in LAYERS},
            "total_surfaced": sum(len(buckets[layer]) for layer in LAYERS),
            "layers": buckets
        })
    return reports


def to_markdown(profile, reports):
    out = []
    out.append("# EXPERIMENT DAY SIMULATION v1")
    out.append("")
    out.append("このレポートは**架空家庭・架空状態**による決定論的シミュレーション。実在利用者の家庭データではない。")
    out.append("")
    out.append("目的は件数を3件等へ固定することではなく、同じ家庭でも状態によって `今見る / 今日の候補 / ルーティン / レビュー` の件数が自然に変動することを検証すること。")
    out.append("")
    out.append(f"Profile: `{profile['profile_id']}`")
    out.append("")
    out.append("## 件数比較")
    out.append("")
    out.append("| シナリオ | 今見る | 今日の候補 | ルーティン | レビュー | 表示対象合計 |")
    out.append("|---|---:|---:|---:|---:|---:|")
    for r in reports:
        c = r["counts"]
        out.append(f"| {r['title']} | {c['now']} | {c['today']} | {c['routine']} | {c['review']} | {r['total_surfaced']} |")
    out.append("")
    out.append("`ルーティン`は授乳・オムツ替え等の反復実行を別ストリームに分けたもので、`今日の候補`の件数を水増ししない。")
    out.append("")
    for r in reports:
        out.append(f"## {r['title']}")
        out.append("")
        out.append(f"Context: {', '.join(r['context_tags'])}")
        out.append("")
        for layer in LAYERS:
            items = r["layers"][layer]
            out.append(f"### {LAYER_JA[layer]} — {len(items)}件")
            out.append("")
            if not items:
                out.append("該当なし。")
                out.append("")
                continue
            out.append("| ID | 項目 | 出した理由 | シナリオ状態 |")
            out.append("|---|---|---|---|")
            for x in items:
                out.append(f"| `{x['id']}` | {x['label']} | {x['reason']} | {x['scenario_note']} |")
            out.append("")
    out.append("## この段階で証明していないこと")
    out.append("")
    out.append("- このシミュレーションの件数自体が適正であること")
    out.append("- 293項目の個別メタデータが最終品質であること")
    out.append("- 健康・安全42項目の人手レビューが完了したこと")
    out.append("- 実際の家庭状態を自動取得できること")
    out.append("")
    out.append("次の実証では、実生活で『出すべきだったのに出なかった』『出したが不要だった』を記録し、見落とし率とノイズ率で調整する。")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", default="artifacts/responsibility_metadata_v1.jsonl")
    ap.add_argument("--profile", default="data/experiment_household_profile_v1.json")
    ap.add_argument("--scenarios", default="data/experiment_scenarios_v1.json")
    ap.add_argument("--json-out", default="artifacts/experiment_day_simulation_v1.json")
    ap.add_argument("--md-out", default="artifacts/experiment_day_simulation_v1.md")
    args = ap.parse_args()

    metadata = read_jsonl(Path(args.metadata))
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    if not profile.get("synthetic"):
        raise SystemExit("experiment profile must be explicitly synthetic")

    reports = simulate(metadata, profile, scenarios)
    payload = {"schema_version": 1, "profile_id": profile["profile_id"], "synthetic": True, "reports": reports}
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.md_out).write_text(to_markdown(profile, reports), encoding="utf-8")

    print(json.dumps({r["id"]: r["counts"] for r in reports}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
