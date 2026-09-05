#!/usr/bin/env python3
import json
from collections import Counter
from pathlib import Path

metadata = [json.loads(line) for line in Path("artifacts/responsibility_metadata_v1.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
by_id = {r["id"]: r for r in metadata}
review = json.loads(Path("data/health_safety_review_v1.json").read_text(encoding="utf-8"))
items = review["items"]

s_ids = {r["id"] for r in metadata if "S" in r["type"].split("/")}
review_ids = {r["id"] for r in items}

assert len(s_ids) == 42, len(s_ids)
assert len(items) == review["expected_items"] == 42
assert len(review_ids) == 42
assert review_ids == s_ids, f"review coverage mismatch missing={sorted(s_ids-review_ids)} extra={sorted(review_ids-s_ids)}"

allowed = set(review["allowed_statuses"])
for item in items:
    assert item["status"] in allowed, item
    meta = by_id[item["id"]]
    assert meta["manual_review_required"] is True
    for source_id in item["required_source_ids"]:
        assert source_id in meta["source_ids"], (item["id"], source_id, meta["source_ids"])

counts = Counter(x["status"] for x in items)
assert counts == Counter({"PASS_DIRECT": 22, "PASS_WITH_BOUNDARY": 19, "REWRITE_OR_SPLIT": 1})
blockers = [x for x in items if x["status"] in {"NEEDS_DIRECT_SOURCE", "REWRITE_OR_SPLIT"}]
assert [x["id"] for x in blockers] == ["SAFE-018"]
assert blockers[0].get("blocker_reason")

print("health/safety review validation: PASS")
print(dict(counts))
print("blockers", [x["id"] for x in blockers])
