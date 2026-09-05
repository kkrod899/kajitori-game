#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="artifacts/responsibility_metadata_v1.jsonl")
    ap.add_argument("--amendments", default="data/responsibility_amendments_v2.json")
    ap.add_argument("--out", default="artifacts/responsibility_catalog_v2.jsonl")
    args = ap.parse_args()

    rows = read_jsonl(Path(args.base))
    amendments = json.loads(Path(args.amendments).read_text(encoding="utf-8"))
    by_id = {row["id"]: dict(row) for row in rows}

    if len(by_id) != len(rows):
        raise SystemExit("duplicate IDs in base catalog")

    for item_id, patch in amendments.get("replacements", {}).items():
        if item_id not in by_id:
            raise SystemExit(f"replacement target missing: {item_id}")
        replacement = dict(by_id[item_id])
        for key, value in patch.items():
            if key == "source_ids_replace":
                replacement["source_ids"] = list(value)
            else:
                replacement[key] = value
        replacement["catalog_schema_version"] = 2
        replacement["amendment_kind"] = "replacement"
        by_id[item_id] = replacement

    for addition in amendments.get("additions", []):
        item_id = addition["id"]
        if item_id in by_id:
            raise SystemExit(f"addition duplicates existing ID: {item_id}")
        row = dict(addition)
        row["catalog_schema_version"] = 2
        row["amendment_kind"] = "addition"
        by_id[item_id] = row

    out = sorted(by_id.values(), key=lambda row: row["id"])
    ids = [row["id"] for row in out]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate IDs in effective catalog")
    if len(out) != len(rows) + len(amendments.get("additions", [])):
        raise SystemExit("effective catalog count mismatch")

    for row in out:
        row.setdefault("catalog_schema_version", 2)
        row.setdefault("amendment_kind", "base")
        if "S" in row["type"].split("/") and not row.get("source_ids"):
            raise SystemExit(f"health/safety item lacks source: {row['id']}")

    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in out:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(json.dumps({
        "base_items": len(rows),
        "effective_items": len(out),
        "replacements": len(amendments.get("replacements", {})),
        "additions": len(amendments.get("additions", [])),
        "health_safety_items": sum("S" in row["type"].split("/") for row in out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
