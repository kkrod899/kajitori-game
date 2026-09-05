#!/usr/bin/env python3
import json
from pathlib import Path

raw = json.loads(Path("artifacts/activation_engine_v2.json").read_text(encoding="utf-8"))
ranked = json.loads(Path("artifacts/activation_engine_v2_ranked.json").read_text(encoding="utf-8"))
assert ranked["attention_ordering_version"] == "lexicographic-v1"
assert ranked["attention_policy"]["no_candidate_truncation"] is True
assert ranked["attention_policy"]["no_fixed_target_count"] is True

raw_reports = {r["id"]: r for r in raw["reports"]}
ranked_reports = {r["id"]: r for r in ranked["reports"]}
assert set(raw_reports) == set(ranked_reports)

for report_id, before in raw_reports.items():
    after = ranked_reports[report_id]
    assert before["counts"] == after["counts"]
    assert before["card_counts"] == after["card_counts"]
    assert {x["id"] for x in before["atomic_candidates"]} == {x["id"] for x in after["atomic_candidates"]}
    assert {x["card_id"] for x in before["cards"]} == {x["card_id"] for x in after["cards"]}
    atomic_keys = [tuple(x["attention_order_key"]) for x in after["atomic_candidates"]]
    card_keys = [tuple(x["attention_order_key"]) for x in after["cards"]]
    assert atomic_keys == sorted(atomic_keys), report_id
    assert card_keys == sorted(card_keys), report_id
    assert all(x["attention_label"] for x in after["atomic_candidates"])
    assert all(x["attention_label"] for x in after["cards"])

high = ranked_reports["high_load_weekday_v2"]
assert high["cards"][0]["layer"] == "now"
assert high["cards"][0]["attention_class"] in {"safety_health_deadline", "safety_health", "deadline"}

print("attention ordering v2 validation: PASS")
for report_id, report in ranked_reports.items():
    print(report_id, [card["attention_class"] for card in report["cards"][:5]])
