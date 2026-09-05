#!/usr/bin/env python3
import json
from pathlib import Path

p = json.loads(Path("artifacts/activation_coverage_v2.json").read_text(encoding="utf-8"))
assert p["catalog_items"] == 294
assert p["rule_referenced_items"] == 173
assert p["uncovered_items"] == 121
assert p["health_safety"]["covered"] == p["health_safety"]["total"] == 43
assert p["by_domain"]["child_safety"]["coverage_ratio"] == 1.0
assert p["by_domain"]["emergency"]["coverage_ratio"] == 1.0
assert p["by_domain"]["home_maintenance"]["coverage_ratio"] == 0.0
assert p["by_domain"]["supplies"]["uncovered"] >= 10
assert p["by_type_marker"]["M"]["uncovered"] > 0
print("activation coverage v2 validation: PASS")
