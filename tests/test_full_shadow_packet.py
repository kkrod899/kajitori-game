#!/usr/bin/env python3
import csv
import json
import subprocess
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as td:
    out=Path(td)/"packet"
    subprocess.run([
        "python3","tools/generate_full_shadow_packet.py",
        "--profile","data/full_shadow_profile.example.json",
        "--day-state","data/full_shadow_day.example.json",
        "--out-dir",str(out)
    ],check=True)
    required={"packet_manifest.json","engine_candidates.json","engine_candidates_night_review.md","night_observations_template.csv"}
    assert required <= {p.name for p in out.iterdir()}
    manifest=json.loads((out/"packet_manifest.json").read_text(encoding="utf-8"))
    assert manifest["mode"]=="shadow_only_not_active_reliance"
    assert set(manifest["files"])==required-{"packet_manifest.json"}
    candidates=json.loads((out/"engine_candidates.json").read_text(encoding="utf-8"))
    assert candidates["mode"]=="shadow_only"
    ids={x["id"] for x in candidates["candidates"]}
    assert "DAYCARE-008" in ids
    assert "LAUN-006" in ids
    assert "EMG-004" in ids
    with (out/"night_observations_template.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    assert len(rows)>=len(candidates["candidates"])+12
    assert any(r["engine_surfaced"]=="no" for r in rows)
print("full shadow packet validation: PASS")
