#!/usr/bin/env python3
import json
from pathlib import Path

PATH = Path("artifacts/responsibility_metadata_v1.jsonl")
rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

assert len(rows) == 293, len(rows)
ids = [r["id"] for r in rows]
assert len(set(ids)) == 293, "duplicate metadata ids"

for r in rows:
    parts = r["type"].split("/")
    assert r["surface_rule"] not in {"always", "fixed_slot", "goal_count"}
    assert "target_count" not in r and "daily_limit" not in r
    if "S" in parts:
        assert r["manual_review_required"] is True, r["id"]
        assert r["source_ids"], r["id"]
        assert r["evidence_rule"]["claim_ceiling"] == "observed_and_recorded_only", r["id"]
        assert "prevented_harm" in r["evidence_rule"].get("forbidden_claims", []), r["id"]
    if "C" in parts:
        assert r["requires_household_config"] is True, r["id"]
        assert r["household_config_fields"], r["id"]
    if "R" in parts:
        assert r["trigger_type"] == "routine", r["id"]
        assert r["surface_rule"] == "routine_stream", r["id"]

# High-impact source mapping checks.
by_id = {r["id"]: r for r in rows}
assert "SRC-SLEEP-001" in by_id["INF-SLEEP-004"]["source_ids"]
assert "SRC-VAX-001" in by_id["CHD-MED-001"]["source_ids"]
assert "SRC-HEAT-001" in by_id["SAFE-018"]["source_ids"]
assert "SRC-CHILDSEAT-001" in by_id["SAFE-011"]["source_ids"]
assert "SRC-BICYCLE-001" in by_id["SAFE-013"]["source_ids"]
assert "SRC-DISASTER-001" in by_id["EMG-004"]["source_ids"]
assert "SRC-ORAL-001" in by_id["OLD-DAILY-003"]["source_ids"]

print("responsibility metadata validation: PASS")
print(f"items={len(rows)} safety_health={sum(r['manual_review_required'] for r in rows)} config_dependent={sum(r['requires_household_config'] for r in rows)}")
