#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

catalog = {r["id"]: r for r in [json.loads(line) for line in Path("artifacts/responsibility_catalog_v2.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]}
health_safety = {item_id for item_id, row in catalog.items() if "S" in row["type"].split("/")}
review_payload = json.loads(Path("data/health_safety_review_v2.json").read_text(encoding="utf-8"))
review = {row["id"]: row for row in review_payload["items"]}
boundary_payload = json.loads(Path("data/health_safety_boundaries_v2.json").read_text(encoding="utf-8"))
boundaries = {row["id"]: row for row in boundary_payload["items"]}

assert health_safety == set(review)
assert len(health_safety) == 43
counts = Counter(row["status"] for row in review.values())
assert counts == Counter({"PASS_DIRECT": 23, "PASS_WITH_BOUNDARY": 20}), counts
assert set(boundaries) == {item_id for item_id, row in review.items() if row["status"] == "PASS_WITH_BOUNDARY"}

for item_id, row in review.items():
    required = set(row.get("required_source_ids", []))
    actual = set(catalog[item_id].get("source_ids", []))
    assert required <= actual, (item_id, required - actual)
    assert row["status"] in {"PASS_DIRECT", "PASS_WITH_BOUNDARY"}
    assert catalog[item_id]["manual_review_required"] is True

for item_id, boundary in boundaries.items():
    assert boundary["required_context_paths"], item_id
    assert boundary["boundary_statement"], item_id
    assert boundary["prohibited_behavior"], item_id

assert review["SAFE-018"]["status"] == "PASS_DIRECT"
assert review["SAFE-018"]["required_source_ids"] == ["SRC-HEAT-001"]
assert review["SAFE-019"]["status"] == "PASS_WITH_BOUNDARY"
assert review["SAFE-019"]["required_source_ids"] == ["SRC-WINTER-WEATHER-001"]
assert "context.weather.official_snow_or_blizzard_warning" in boundaries["SAFE-019"]["required_context_paths"]
assert "context.outing.transport_context_available" in boundaries["SAFE-019"]["required_context_paths"]

print("health and safety v2 validation: PASS")
print("status_counts", dict(counts), "boundary_rules", len(boundaries))
