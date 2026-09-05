#!/usr/bin/env python3
import json
from pathlib import Path

spec = json.loads(Path("data/shadow_intake_spec_v2.json").read_text(encoding="utf-8"))
registry = json.loads(Path("artifacts/raw_state_field_registry_v2.json").read_text(encoding="utf-8"))
profile = json.loads(Path("data/experiment_household_profile_v1.json").read_text(encoding="utf-8"))
registry_by_path = {row["path"]: row for row in registry["fields"]}
capabilities = set(profile.get("tags", []))
capabilities.update(k for k, v in profile.get("household_config", {}).items() if v is True)

assert spec["schema_version"] == 2
assert spec["privacy_rule"] == "responses_local_only_never_commit_to_public_repo"
sections = {s["id"]: s for s in spec["sections"]}
assert {"schedule", "infant", "household", "capacity", "events", "external", "weekly"} <= set(sections)

all_fields = []
for section in spec["sections"]:
    assert section["cadence"] in {"morning", "event_only", "automatic_or_manual_lookup", "periodic"}
    for field in section["fields"]:
        all_fields.append((section, field))
        assert field["path"] in registry_by_path, field["path"]
        assert "required" in field and "default" in field

# Event and periodic observations are not forced into the daily morning burden.
for section_id in ("events", "weekly"):
    assert all(not field["required"] for field in sections[section_id]["fields"])

# Official weather fields must be identified as official-external raw facts.
for field in sections["external"]["fields"]:
    assert registry_by_path[field["path"]]["source_class"] == "official_external_state"

# Count only fields visible for the synthetic profile and always shown at morning cadence.
def gate_ok(section, field):
    gate = field.get("profile_gate") or section.get("profile_gate")
    return gate is None or gate in capabilities

morning_visible = [
    field for section, field in all_fields
    if section["cadence"] == "morning" and gate_ok(section, field) and "show_if" not in field
]
required_morning = [field for field in morning_visible if field["required"]]
assert len(morning_visible) <= 24, len(morning_visible)
assert len(required_morning) <= 18, len(required_morning)

# The intake contract must not request direct medical diagnosis or sensitive document content.
for _, field in all_fields:
    text = (field.get("label", "") + " " + field.get("help", "")).lower()
    assert "診断名" not in text
    assert "保険証画像" not in text

print("shadow intake spec v2 validation: PASS")
print(f"morning_visible={len(morning_visible)} required_morning={len(required_morning)} total_fields={len(all_fields)}")
