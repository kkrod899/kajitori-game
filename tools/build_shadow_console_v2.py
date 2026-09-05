#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def safe_inline_json(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return text.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default="experiments/shadow-console-v2/template.html")
    ap.add_argument("--css", default="experiments/shadow-console-v2/shadow.css")
    ap.add_argument("--js", default="experiments/shadow-console-v2/shadow.js")
    ap.add_argument("--catalog", default="artifacts/responsibility_catalog_v2.jsonl")
    ap.add_argument("--rules", default="artifacts/activation_rules_core_v2.json")
    ap.add_argument("--bundles", default="artifacts/surface_bundles_v2.json")
    ap.add_argument("--review", default="data/health_safety_review_v2.json")
    ap.add_argument("--boundaries", default="data/health_safety_boundaries_v2.json")
    ap.add_argument("--registry", default="artifacts/raw_state_registry_v2.json")
    ap.add_argument("--intake", default="data/shadow_intake_spec_v2.json")
    ap.add_argument("--out", default="artifacts/shadow_console_v2.html")
    args = ap.parse_args()

    source_paths = [
        Path(args.template), Path(args.css), Path(args.js), Path(args.catalog),
        Path(args.rules), Path(args.bundles), Path(args.review),
        Path(args.boundaries), Path(args.registry), Path(args.intake),
    ]
    for path in source_paths:
        if not path.exists():
            raise SystemExit(f"missing shadow-console source: {path}")

    catalog = read_jsonl(Path(args.catalog))
    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
    bundles = json.loads(Path(args.bundles).read_text(encoding="utf-8"))
    review = json.loads(Path(args.review).read_text(encoding="utf-8"))
    boundaries = json.loads(Path(args.boundaries).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    intake = json.loads(Path(args.intake).read_text(encoding="utf-8"))

    digest = hashlib.sha256()
    for path in source_paths:
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    build_id = digest.hexdigest()

    embedded = {
        "build": {
            "id": build_id,
            "schema_version": 2,
            "catalog_items": len(catalog),
            "rules": len(rules.get("rules", [])),
            "raw_state_fields": registry.get("field_count"),
            "privacy_default": "local_only",
            "network_runtime": "blocked_by_csp",
        },
        "catalog": catalog,
        "rules": rules,
        "bundles": bundles,
        "review": review,
        "boundaries": boundaries,
        "registry": registry,
        "intakeSpec": intake,
    }

    template = Path(args.template).read_text(encoding="utf-8")
    html = template.replace("__SHADOW_CSS__", Path(args.css).read_text(encoding="utf-8"))
    html = html.replace("__EMBEDDED_DATA__", safe_inline_json(embedded))
    html = html.replace("__SHADOW_JS__", Path(args.js).read_text(encoding="utf-8"))
    if any(token in html for token in ("__SHADOW_CSS__", "__EMBEDDED_DATA__", "__SHADOW_JS__")):
        raise SystemExit("shadow-console template replacement incomplete")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    print(json.dumps({
        "output": str(out),
        "bytes": out.stat().st_size,
        "build_id": build_id,
        "catalog_items": len(catalog),
        "rules": len(rules.get("rules", [])),
        "single_file": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
