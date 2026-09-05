#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


catalog = read_jsonl("artifacts/responsibility_catalog_v2.jsonl")
by_id = {row["id"]: row for row in catalog}
assert len(catalog) == 294
assert len(by_id) == 294

assert by_id["SAFE-018"]["label"] == "暑熱時の外出リスクを確認する"
assert by_id["SAFE-018"]["trigger_type"] == "safety"
assert by_id["SAFE-018"]["source_ids"] == ["SRC-HEAT-001"]
assert by_id["SAFE-018"]["metadata_maturity"] == "reviewed_v2"

assert by_id["SAFE-019"]["label"] == "大雪・暴風雪時の外出・移動リスクを確認する"
assert by_id["SAFE-019"]["source_ids"] == ["SRC-WINTER-WEATHER-001"]
assert "guaranteed_safe_travel" in by_id["SAFE-019"]["evidence_rule"]["forbidden_claims"]

s_ids = {row["id"] for row in catalog if "S" in row["type"].split("/")}
assert len(s_ids) == 43

review = json.loads(Path("data/health_safety_review_v2.json").read_text(encoding="utf-8"))
review_ids = {row["id"] for row in review["items"]}
assert review["expected_items"] == 43
assert review_ids == s_ids
counts = Counter(row["status"] for row in review["items"])
assert counts == Counter({"PASS_DIRECT": 23, "PASS_WITH_BOUNDARY": 20})
assert not [row for row in review["items"] if row["status"] in review["blocking_statuses"]]

review_by_id = {row["id"]: row for row in review["items"]}
assert review_by_id["SAFE-018"]["status"] == "PASS_DIRECT"
assert review_by_id["SAFE-019"]["status"] == "PASS_WITH_BOUNDARY"
assert review_by_id["SAFE-019"]["required_source_ids"] == ["SRC-WINTER-WEATHER-001"]

boundaries = json.loads(Path("data/health_safety_boundaries_v2.json").read_text(encoding="utf-8"))["items"]
boundary_ids = {row["id"] for row in review["items"] if row["status"] == "PASS_WITH_BOUNDARY"}
assert len(boundaries) == 20
assert set(boundaries) == boundary_ids
assert "context.weather.official_snow_or_blizzard_warning" in boundaries["SAFE-019"]["required_context_paths"]

source_amendments = json.loads(Path("data/source_registry_amendments_v2.json").read_text(encoding="utf-8"))
source = source_amendments["sources"]["SRC-WINTER-WEATHER-001"]
assert "SAFE-019" in source["supports"]
assert all(url.startswith("https://") for url in source["urls"])

print("responsibility catalog v2 validation: PASS")
print(dict(counts))
