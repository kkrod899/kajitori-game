#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROW_RE = re.compile(r"^\|\s*([A-Z0-9-]+)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$")

INVENTORY_WORDS = ("在庫","残量","不足","補充","足りる","届く","定期購入")
SCHEDULE_WORDS = ("予約","予定","時刻","締切","期限","回収日","日程","申請","更新書類","当日","翌日","明日","1週間")
HANDOFF_WORDS = ("引き継","共有","担当を決め","担当を確認","衝突を解消","バックアップ担当")
LIFECYCLE_WORDS = ("サイズアウト","サイズ変更","成長","季節","衣替え","行事","イベント用品","買い替え","交換時期")
MAINTENANCE_WORDS = ("フィルター","清掃","手入れ","修理","故障","カビ","結露","整理","片付け","定位置","衛生的","洗浄","交換要否","破損","劣化")
STATE_WORDS = ("確認","把握","気づく","判断","管理","状態","要否","崩れて","変化")

GROUP_REVIEW_DAYS = {
    "INF-FEED": 2, "INF-DIAP": 2, "INF-SLEEP": 1, "INF-HYG": 3,
    "CHD-MED": 7, "SAFE": 14, "OLD-DAILY": 3, "DAYCARE": 1,
    "FOOD": 2, "KIT": 3, "LAUN": 2, "CLEAN": 7, "SUP": 7,
    "WASTE": 1, "PLAN": 1, "ADMIN": 7, "HOME": 14, "EMG": 30,
    "FAM": 1, "GROW": 14, "PLAY": 7,
}

ESSENTIAL_ROUTINE_GROUPS = {"INF-FEED","INF-DIAP","INF-SLEEP","INF-HYG","OLD-DAILY","DAYCARE","FOOD"}


def parse_master(path: Path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        item_id, type_text, label = [x.strip() for x in m.groups()]
        if item_id == "ID" or not item_id.strip("-"):
            continue
        rows.append({"id": item_id, "type": type_text, "label": label})
    return rows


def group_for(item_id: str, group_defaults: dict) -> str:
    matches = [g for g in group_defaults if item_id == g or item_id.startswith(g + "-")]
    if not matches:
        raise ValueError(f"No group rule for {item_id}")
    return max(matches, key=len)


def merge_unique(a, b):
    out = []
    for x in (a or []) + (b or []):
        if x not in out:
            out.append(x)
    return out


def apply_pattern_overrides(item_id: str, base: dict, mapping: dict):
    for key, value in mapping.items():
        if key.endswith("*") and item_id.startswith(key[:-1]):
            if isinstance(value, dict):
                for k, v in value.items():
                    if k in ("source_ids", "applicability"):
                        base[k] = merge_unique(base.get(k, []), v)
                    else:
                        base[k] = v
            elif isinstance(value, list):
                base = merge_unique(base, value)
    if item_id in mapping:
        value = mapping[item_id]
        if isinstance(value, dict):
            for k, v in value.items():
                if k in ("source_ids", "applicability"):
                    base[k] = merge_unique(base.get(k, []), v)
                else:
                    base[k] = v
        elif isinstance(value, list):
            base = merge_unique(base, value)
    return base


def classify_trigger(item):
    label, t = item["label"], item["type"]
    if "R" in t.split("/"):
        return "routine"
    if any(w in label for w in INVENTORY_WORDS):
        return "inventory"
    if any(w in label for w in SCHEDULE_WORDS):
        return "schedule"
    if any(w in label for w in HANDOFF_WORDS):
        return "handoff"
    if any(w in label for w in LIFECYCLE_WORDS):
        return "lifecycle"
    if "S" in t.split("/"):
        if any(w in label for w in ("発熱","咳","嘔吐","尿","便","発達","食事等","アレルギー")):
            return "health_state"
        return "safety"
    if any(w in label for w in MAINTENANCE_WORDS):
        return "maintenance"
    if any(w in label for w in STATE_WORDS):
        return "state"
    return "task_state"


def cadence_for(trigger, group):
    if trigger == "routine":
        return {"mode": "each_occurrence"}
    if trigger == "inventory":
        return {"mode": "state_threshold", "review_interval_days": GROUP_REVIEW_DAYS[group]}
    if trigger == "schedule":
        return {"mode": "deadline_or_event", "review_interval_days": 1}
    if trigger == "handoff":
        return {"mode": "transition_or_daily", "review_interval_days": 1}
    if trigger == "lifecycle":
        return {"mode": "change_or_periodic", "review_interval_days": GROUP_REVIEW_DAYS[group]}
    if trigger in ("safety", "health_state"):
        return {"mode": "context_change_or_periodic", "review_interval_days": GROUP_REVIEW_DAYS[group]}
    if trigger == "maintenance":
        return {"mode": "periodic_or_state", "review_interval_days": GROUP_REVIEW_DAYS[group]}
    return {"mode": "state_or_review", "review_interval_days": GROUP_REVIEW_DAYS[group]}


def priority_for(item, trigger, group):
    parts = item["type"].split("/")
    if "S" in parts:
        return "safety_health"
    if trigger == "schedule":
        return "deadline"
    if trigger == "inventory" and group in {"INF-FEED","INF-DIAP","DAYCARE","FOOD"}:
        return "high"
    if trigger == "routine" and group in ESSENTIAL_ROUTINE_GROUPS:
        return "essential_routine"
    if group == "FAM" and item["id"] in {"FAM-003","FAM-004","FAM-005","FAM-006","FAM-007"}:
        return "capacity"
    if trigger in {"state","health_state","task_state"} and group in {"INF-FEED","INF-DIAP","INF-SLEEP","CHD-MED","DAYCARE"}:
        return "high"
    return "maintenance"


def surface_for(trigger, priority):
    if trigger == "routine":
        return "routine_stream"
    if priority == "safety_health":
        return "now_if_triggered_else_review"
    if priority == "deadline":
        return "now_if_due_24h_else_today_if_due"
    if trigger == "inventory":
        return "today_if_threshold"
    if trigger == "handoff":
        return "transition_or_evening"
    if trigger in ("lifecycle", "maintenance"):
        return "review_if_due"
    return "today_if_unknown_changed_or_due"


def state_inputs_for(trigger):
    return {
        "routine": ["completed_at"],
        "inventory": ["remaining_level","coverage_until","replenishment_status"],
        "schedule": ["due_at","owner","prep_status","closed"],
        "handoff": ["handoff_status","open_loops"],
        "lifecycle": ["current_fit","change_signal","next_action"],
        "safety": ["safe_status","hazard_present","action_taken"],
        "health_state": ["observed_state","changed_from_usual","consultation_status"],
        "maintenance": ["condition","next_due_at","action_status"],
        "state": ["current_state","changed_from_usual","next_action"],
        "task_state": ["current_state","next_action"],
    }[trigger]


def close_for(label, trigger):
    if trigger == "routine":
        return f"「{label}」を実行し、必要な後片付けまたは次工程が残っていない"
    if trigger == "inventory":
        return "残量を確認し、次の必要期間を満たすか、補充・購入の具体的な次アクションを確定する"
    if trigger == "schedule":
        return "日時・担当・必要準備・締切を確認し、未確定事項をなくす"
    if trigger == "handoff":
        return "相手が追加質問なしで次対応できる情報を共有する"
    if trigger == "lifecycle":
        return "現在の適合状態を確認し、対応不要または期限付きの更新アクションを確定する"
    if trigger == "safety":
        return "危険要因の有無を確認し、問題があれば除去・回避・専門相談のいずれかへつなぐ"
    if trigger == "health_state":
        return "観察できた状態を記録し、必要に応じて受診・相談等の次アクションを確定する"
    if trigger == "maintenance":
        return "状態を確認し、必要対応を実施するか期限付きの次アクションを作る"
    return "現状を確認し、対応不要または次アクションを確定する"


def evidence_for(item, trigger):
    if "S" in item["type"].split("/"):
        return {"required":["state_snapshot"],"optional":["action_record","consultation_record"],"claim_ceiling":"observed_and_recorded_only","forbidden_claims":["prevented_harm","medical_diagnosis_without_source"]}
    if trigger == "routine":
        return {"required":["completion_event"],"claim_ceiling":"completed_only"}
    if trigger == "inventory":
        return {"required":["state_snapshot"],"optional":["replenishment_action"],"claim_ceiling":"state_and_recorded_action_only"}
    if trigger == "schedule":
        return {"required":["deadline_snapshot"],"optional":["completion_event"],"claim_ceiling":"scheduled_or_completed_only"}
    if trigger == "handoff":
        return {"required":["handoff_event"],"claim_ceiling":"shared_only"}
    return {"required":["state_snapshot"],"optional":["action_record"],"claim_ceiling":"observed_and_recorded_only"}


def default_visibility(trigger, priority):
    if trigger == "routine":
        return "collapsed_routine"
    if priority == "safety_health":
        return "hidden_until_context_or_review_due"
    if priority == "deadline":
        return "hidden_until_horizon"
    return "hidden_until_due"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default="docs/RESPONSIBILITY_MASTER_V1.md")
    ap.add_argument("--rules", default="data/responsibility_metadata_rules_v1.json")
    ap.add_argument("--out", default="artifacts/responsibility_metadata_v1.jsonl")
    args = ap.parse_args()

    master = parse_master(Path(args.master))
    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    expected = rules["master_expected_count"]
    if len(master) != expected:
        raise SystemExit(f"master count mismatch: {len(master)} != {expected}")
    ids = [x["id"] for x in master]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate IDs in master")

    out = []
    for item in master:
        group = group_for(item["id"], rules["group_defaults"])
        base = dict(rules["group_defaults"][group])
        base["source_ids"] = list(base.get("source_ids", []))
        base["applicability"] = list(base.get("applicability", []))
        base = apply_pattern_overrides(item["id"], base, rules.get("id_overrides", {}))

        config_fields = []
        for key, value in rules.get("household_config_overrides", {}).items():
            if key.endswith("*") and item["id"].startswith(key[:-1]):
                config_fields = merge_unique(config_fields, value)
        if item["id"] in rules.get("household_config_overrides", {}):
            config_fields = merge_unique(config_fields, rules["household_config_overrides"][item["id"]])

        trigger = classify_trigger(item)
        priority = priority_for(item, trigger, group)
        meta = {
            "id": item["id"],
            "label": item["label"],
            "type": item["type"],
            "group": group,
            "domain": base["domain"],
            "applicability": base["applicability"],
            "requires_household_config": ("C" in item["type"].split("/")),
            "household_config_fields": config_fields,
            "trigger_type": trigger,
            "cadence": cadence_for(trigger, group),
            "priority_class": priority,
            "surface_rule": surface_for(trigger, priority),
            "close_condition": close_for(item["label"], trigger),
            "state_inputs": state_inputs_for(trigger),
            "evidence_rule": evidence_for(item, trigger),
            "source_class": base["source_class"],
            "source_ids": base.get("source_ids", []),
            "default_visibility": default_visibility(trigger, priority),
            "manual_review_required": ("S" in item["type"].split("/")),
            "metadata_maturity": "generated_v1"
        }
        if "S" in item["type"].split("/") and not meta["source_ids"]:
            raise SystemExit(f"safety/health item lacks source: {item['id']}")
        if "C" in item["type"].split("/") and not meta["household_config_fields"]:
            meta["household_config_fields"] = ["household_or_local_rule"]
        out.append(meta)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.out).open("w", encoding="utf-8") as f:
        for row in out:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    counts = {}
    for row in out:
        counts[row["trigger_type"]] = counts.get(row["trigger_type"], 0) + 1
    print(json.dumps({
        "items": len(out),
        "manual_review_required": sum(x["manual_review_required"] for x in out),
        "config_dependent": sum(x["requires_household_config"] for x in out),
        "trigger_counts": counts
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
