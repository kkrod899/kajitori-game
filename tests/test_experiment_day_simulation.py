#!/usr/bin/env python3
import json
from pathlib import Path

p = Path("artifacts/experiment_day_simulation_v1.json")
payload = json.loads(p.read_text(encoding="utf-8"))
assert payload["synthetic"] is True
reports = {r["id"]: r for r in payload["reports"]}
assert set(reports) == {"normal_weekday", "high_load_weekday", "low_load_weekend"}

app = payload["applicability_summary"]
assert app["master_count"] == 293
assert app["structurally_applicable_count"] < 293, "feature-gated items should be excluded"
assert app["excluded_count"] >= 4
assert app["item_level_applicability_review_complete"] is False
# Structural applicability ratio is descriptive only; it is not an acceptance threshold.
assert 0 < app["structurally_applicable_ratio"] <= 1

normal = reports["normal_weekday"]
high = reports["high_load_weekday"]
low = reports["low_load_weekend"]

# No fixed-three behavior: the system should surface variable counts from state.
assert normal["counts"] == {"now": 2, "today": 18, "routine": 19, "review": 5}
assert high["counts"] == {"now": 6, "today": 27, "routine": 19, "review": 6}
assert low["counts"] == {"now": 0, "today": 11, "routine": 16, "review": 4}
assert high["counts"]["now"] > normal["counts"]["now"]
assert high["counts"]["today"] > low["counts"]["today"]

# Repeated care must be separated from today's management candidates.
for r in reports.values():
    assert r["counts"]["routine"] >= 10
    ids = []
    for layer in ("now", "today", "routine", "review"):
        ids.extend(x["id"] for x in r["layers"][layer])
    assert len(ids) == len(set(ids)), f"duplicate surfaced item in {r['id']}"

# Safety/health items that surface must be reviewed, sourced, and not blocked.
for r in reports.values():
    for layer in ("now", "today", "review"):
        for item in r["layers"][layer]:
            if item["manual_review_required"]:
                assert item["source_ids"], item["id"]
                assert item["health_safety_review_status"] in {"PASS_DIRECT", "PASS_WITH_BOUNDARY"}, item

# Stress scenario: boundary-ready vaccination preparation can surface, blocked SAFE-018 cannot.
high_now = {x["id"] for x in high["layers"]["now"]}
assert "CHD-MED-003" in high_now
assert "FAM-004" in high_now
assert "SAFE-018" not in high_now
suppressed = {x["id"]: x["reason"] for x in high["suppressed"]}
assert high["suppressed_count"] == 1
assert suppressed["SAFE-018"] == "manual_review_status=REWRITE_OR_SPLIT"

# Weekend recovery scenario intentionally has no daycare items.
low_ids = {x["id"] for layer in low["layers"].values() for x in layer}
assert not any(x.startswith("DAYCARE-") for x in low_ids)

print("experiment day simulation validation: PASS")
print("structural_applicability", app["structurally_applicable_count"], "/", app["master_count"])
for r in (normal, high, low):
    print(r["id"], r["counts"], "suppressed=", r["suppressed_count"])
