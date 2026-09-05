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
assert app["coarsely_applicable_count"] < 293, "feature-gated items should be excluded"
assert app["excluded_count"] >= 4
# This warning is intentional at v1: it proves the next gate is item-level applicability refinement,
# rather than pretending group-level filtering is production-ready.
assert app["coarse_applicability_warning"] is True

normal = reports["normal_weekday"]
high = reports["high_load_weekday"]
low = reports["low_load_weekend"]

# No fixed-three behavior: the system should surface variable counts from state.
assert normal["counts"]["now"] >= 1
assert high["counts"]["now"] > normal["counts"]["now"]
assert low["counts"]["now"] == 0
assert high["counts"]["today"] > low["counts"]["today"]
assert len({normal["counts"]["today"], high["counts"]["today"], low["counts"]["today"]}) >= 2

# Repeated care must be separated from today's management candidates.
for r in reports.values():
    assert r["counts"]["routine"] >= 10
    ids = []
    for layer in ("now", "today", "routine", "review"):
        ids.extend(x["id"] for x in r["layers"][layer])
    assert len(ids) == len(set(ids)), f"duplicate surfaced item in {r['id']}"

# Safety/health items that surface still carry source coverage.
for r in reports.values():
    for layer in ("now", "today", "review"):
        for item in r["layers"][layer]:
            if item["manual_review_required"]:
                assert item["source_ids"], item["id"]

# Stress scenario must bring actual safety/health and capacity signals into Now.
high_now = {x["id"] for x in high["layers"]["now"]}
assert "SAFE-018" in high_now
assert "CHD-MED-003" in high_now
assert "FAM-004" in high_now

# Weekend recovery scenario intentionally has no daycare items.
low_ids = {x["id"] for layer in low["layers"].values() for x in layer}
assert not any(x.startswith("DAYCARE-") for x in low_ids)

print("experiment day simulation validation: PASS")
print("coarse_applicability", app["coarsely_applicable_count"], "/", app["master_count"], "warning=", app["coarse_applicability_warning"])
for r in (normal, high, low):
    print(r["id"], r["counts"])
