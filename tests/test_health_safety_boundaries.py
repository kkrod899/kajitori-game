#!/usr/bin/env python3
import json
from pathlib import Path

review = json.loads(Path("data/health_safety_review_v1.json").read_text(encoding="utf-8"))
boundaries = json.loads(Path("data/health_safety_boundaries_v1.json").read_text(encoding="utf-8"))["items"]

boundary_ids = {x["id"] for x in review["items"] if x["status"] == "PASS_WITH_BOUNDARY"}
assert len(boundary_ids) == 19
assert set(boundaries) == boundary_ids, f"boundary coverage mismatch missing={sorted(boundary_ids-set(boundaries))} extra={sorted(set(boundaries)-boundary_ids)}"

for item_id, rule in boundaries.items():
    assert rule["activation_gate"].strip(), item_id
    assert rule["required_context_fields"], item_id
    assert rule["forbidden_auto_actions"], item_id

# Explicit protections for the most consequential boundary items.
assert "infer_due_date_from_age_only" in boundaries["CHD-MED-001"]["forbidden_auto_actions"]
assert "diagnose" in boundaries["CHD-MED-008"]["forbidden_auto_actions"]
assert "assume_8000_available_now_without_local_hours" in boundaries["CHD-MED-009"]["forbidden_auto_actions"]
assert "store_sensitive_document_content_without_explicit_secure_design" in boundaries["EMG-008"]["forbidden_auto_actions"]

print("health/safety boundary validation: PASS")
print("boundary_items=19")
