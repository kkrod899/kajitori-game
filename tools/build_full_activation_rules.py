#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

TRIGGER_SIGNAL_MAP = {
    "routine": ["occurrence_due"],
    "inventory": ["threshold_breached", "critical_shortage", "review_due"],
    "schedule": ["due_within_horizon", "hard_deadline_risk", "owner_or_prep_unknown", "review_due"],
    "handoff": ["transition_due", "handoff_incomplete", "open_loops_present"],
    "lifecycle": ["fit_or_stage_changed", "context_changed", "review_due"],
    "safety": ["hazard_present", "context_changed", "review_due"],
    "health_state": ["health_changed", "state_changed", "review_due"],
    "maintenance": ["condition_changed", "maintenance_overdue", "review_due"],
    "state": ["state_unknown", "state_changed", "action_required", "review_due"],
    "task_state": ["action_required", "open_loop_detected", "review_due"]
}

SUPPRESSION_SIGNALS = ["confirmed_not_due", "already_closed", "snoozed_until_future", "not_applicable_now"]


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def merge_unique(*parts):
    out = []
    for part in parts:
        for value in part or []:
            if value not in out:
                out.append(value)
    return out


def layer_policy(meta):
    trigger = meta["trigger_type"]
    priority = meta["priority_class"]
    if trigger == "routine":
        return {"default":"routine", "urgent":"routine", "review":"routine"}
    if priority.startswith("safety_health"):
        return {"default":"review", "urgent":"now", "review":"review"}
    if trigger == "schedule":
        return {"default":"today", "urgent":"now", "review":"review"}
    if trigger == "inventory":
        return {"default":"today", "urgent":"now", "review":"review"}
    if trigger == "handoff":
        return {"default":"today", "urgent":"now", "review":"today"}
    if trigger in {"lifecycle","maintenance"}:
        return {"default":"today", "urgent":"today", "review":"review"}
    return {"default":"today", "urgent":"now", "review":"review"}


def repeat_policy(meta):
    cadence = meta.get("cadence", {})
    mode = cadence.get("mode")
    days = cadence.get("review_interval_days")
    if mode == "each_occurrence":
        return {"repeat":"each_occurrence", "cooldown_hours":0}
    if days:
        return {"repeat":"after_state_change_or_interval", "review_interval_days":days}
    return {"repeat":"after_state_change", "review_interval_days":None}


def build_remaining_rule(meta, policy):
    group = meta["group"]
    defaults = policy["group_defaults"][group]
    override = policy.get("item_overrides", {}).get(meta["id"], {})
    profile_tags = merge_unique(defaults.get("profile_tags"), override.get("profile_tags"))
    feature_flags = merge_unique(defaults.get("default_feature_flags"), override.get("feature_flags"))
    feature_flags_any = merge_unique(override.get("feature_flags_any"))
    config_fields = merge_unique(defaults.get("config_fields"), override.get("config_fields"), meta.get("household_config_fields"))
    trigger = meta["trigger_type"]
    signals = list(TRIGGER_SIGNAL_MAP[trigger])
    return {
        "schema_version": 1,
        "id": meta["id"],
        "label": meta["label"],
        "group": group,
        "domain": meta["domain"],
        "type": meta["type"],
        "rule_origin": "remaining_scope_constrained_v1",
        "profile_gate": {"all_tags":profile_tags},
        "age_gate": override.get("age_gate", defaults.get("age_gate")),
        "feature_gate": {"all":feature_flags, "any":feature_flags_any},
        "config_gate": {"required_fields":config_fields if meta.get("requires_household_config") or config_fields else []},
        "signal_namespace": f"responsibility_state.{meta['id']}",
        "activation_operator": "any",
        "activation_signals": signals,
        "urgent_signals": [x for x in signals if x in {"critical_shortage","hard_deadline_risk","hazard_present","health_changed"}],
        "review_signals": ["review_due"] if "review_due" in signals else [],
        "suppression_signals": list(SUPPRESSION_SIGNALS),
        "layer_policy": layer_policy(meta),
        "repeat_policy": repeat_policy(meta),
        "close_condition": meta["close_condition"],
        "state_inputs": meta["state_inputs"],
        "evidence_rule": meta["evidence_rule"],
        "source_ids": meta.get("source_ids", []),
        "manual_review_required": meta.get("manual_review_required", False),
        "health_safety_review_status": None,
        "boundary_rule_required": False,
        "maturity_ceiling": policy["maturity_ceiling"]
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", default="artifacts/responsibility_metadata_v1.jsonl")
    ap.add_argument("--high-impact", default="artifacts/high_impact_activation_rules_v1.jsonl")
    ap.add_argument("--remaining-policy", default="data/remaining_activation_policy_v1.json")
    ap.add_argument("--out", default="artifacts/full_activation_rules_v1.jsonl")
    args = ap.parse_args()

    metadata = read_jsonl(Path(args.metadata))
    high = read_jsonl(Path(args.high_impact))
    policy = json.loads(Path(args.remaining_policy).read_text(encoding="utf-8"))
    high_by_id = {x["id"]:x for x in high}
    scope_groups = set(policy["scope_groups"])
    remaining = [m for m in metadata if m["group"] in scope_groups]
    if len(remaining) != policy["expected_count"]:
        raise SystemExit(f"remaining scope mismatch: {len(remaining)} != {policy['expected_count']}")

    out = []
    for meta in metadata:
        if meta["id"] in high_by_id:
            rule = dict(high_by_id[meta["id"]])
            rule.setdefault("rule_origin", "high_impact_explicit_v1")
            rule.setdefault("signal_namespace", f"responsibility_state.{meta['id']}")
            out.append(rule)
        elif meta["group"] in scope_groups:
            out.append(build_remaining_rule(meta, policy))
        else:
            raise SystemExit(f"item not covered by high-impact or remaining policy: {meta['id']}")

    if len(out) != len(metadata):
        raise SystemExit(f"full rule count mismatch: {len(out)} != {len(metadata)}")
    ids = [x["id"] for x in out]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate full activation rule IDs")
    write_jsonl(Path(args.out), out)
    origins = {}
    for row in out:
        origins[row["rule_origin"]] = origins.get(row["rule_origin"], 0) + 1
    print(json.dumps({"items":len(out),"origins":origins}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
