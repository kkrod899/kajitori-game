#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

LAYERS = ["now","today","routine","review"]


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def capabilities(profile):
    caps = set(profile.get("tags", []))
    caps.update(k for k,v in profile.get("features", {}).items() if v is True)
    return caps


def gate_rule(rule, profile):
    caps = capabilities(profile)
    missing_tags = [x for x in rule.get("profile_gate", {}).get("all_tags", []) if x not in caps]
    if missing_tags:
        return False, "profile_gate", missing_tags
    feature = rule.get("feature_gate", {})
    missing_all = [x for x in feature.get("all", []) if x not in caps]
    if missing_all:
        return False, "feature_gate_all", missing_all
    any_flags = feature.get("any", [])
    if any_flags and not any(x in caps for x in any_flags):
        return False, "feature_gate_any", any_flags
    config = profile.get("household_config", {})
    missing_config = [x for x in rule.get("config_gate", {}).get("required_fields", []) if x not in config]
    if missing_config:
        return False, "config_gate", missing_config
    age = rule.get("age_gate")
    if age:
        subject = age.get("subject")
        months = profile.get("ages_months", {}).get(subject)
        if months is None:
            return False, "age_unknown", [subject]
        if age.get("min_months") is not None and months < age["min_months"]:
            return False, "age_below", [str(age["min_months"])]
        if age.get("max_months") is not None and months > age["max_months"]:
            return False, "age_above", [str(age["max_months"])]
    return True, "", []


def choose_layer(rule, signals):
    urgent = set(rule.get("urgent_signals", [])) & signals
    review = set(rule.get("review_signals", [])) & signals
    policy = rule.get("layer_policy", {})
    if urgent:
        return policy.get("urgent", policy.get("default", "today")), sorted(urgent)
    non_review = set(rule.get("activation_signals", [])) - set(rule.get("review_signals", []))
    if review and not (non_review & signals):
        return policy.get("review", policy.get("default", "review")), sorted(review)
    return policy.get("default", "today"), sorted(signals & set(rule.get("activation_signals", [])))


def evaluate(rules, day):
    profile = day["profile"]
    by_id = {x["id"]:x for x in rules}
    candidates = []
    suppressed = []
    for item_id, signal_obj in day.get("signals", {}).items():
        if item_id not in by_id:
            suppressed.append({"id":item_id,"reason":"unknown_item"})
            continue
        rule = by_id[item_id]
        ok, reason, detail = gate_rule(rule, profile)
        if not ok:
            suppressed.append({"id":item_id,"reason":reason,"detail":detail})
            continue
        true_signals = {k for k,v in signal_obj.items() if v is True}
        blocked = true_signals & set(rule.get("suppression_signals", []))
        if blocked:
            suppressed.append({"id":item_id,"reason":"runtime_suppression","detail":sorted(blocked)})
            continue
        matched = true_signals & set(rule.get("activation_signals", []))
        op = rule.get("activation_operator", "any")
        active = bool(matched) if op == "any" else set(rule.get("activation_signals", [])) <= true_signals
        if not active:
            suppressed.append({"id":item_id,"reason":"activation_not_met","detail":sorted(true_signals)})
            continue
        layer, reason_signals = choose_layer(rule, true_signals)
        candidates.append({
            "id":item_id,
            "label":rule["label"],
            "group":rule["group"],
            "domain":rule["domain"],
            "layer":layer,
            "matched_signals":reason_signals,
            "close_condition":rule["close_condition"],
            "claim_ceiling":rule.get("evidence_rule", {}).get("claim_ceiling"),
            "maturity_ceiling":rule.get("maturity_ceiling")
        })
    order = {x:i for i,x in enumerate(LAYERS)}
    candidates.sort(key=lambda x:(order.get(x["layer"],99),x["group"],x["id"]))
    return {"schema_version":1,"date":day.get("date"),"mode":"shadow_only","counts":{x:sum(c["layer"]==x for c in candidates) for x in LAYERS},"candidates":candidates,"suppressed":suppressed}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rules",default="artifacts/full_activation_rules_v1.jsonl")
    ap.add_argument("--day",required=True)
    ap.add_argument("--out",default="artifacts/full_day_evaluation_v1.json")
    args=ap.parse_args()
    payload=evaluate(read_jsonl(Path(args.rules)),json.loads(Path(args.day).read_text(encoding="utf-8")))
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(payload["counts"],ensure_ascii=False))

if __name__=="__main__":
    main()
