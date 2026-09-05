#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FIELD_ADDITIONS = [
    {"group":"園・予定","id":"daycare_deadline_closed","label":"園の締切対応は完了","path":"daycare.deadline_closed","type":"tri"},
    {"group":"園・予定","id":"medical_prep","label":"病院・予防接種の外出準備は完了","path":"events.medical.prep_complete","type":"tri"},
    {"group":"園・予定","id":"admin_deadline_closed","label":"行政・書類の期限対応は完了","path":"household.admin.deadline_closed","type":"tri"},
    {"group":"家の運営","id":"food_purchase_required","label":"食品の購入・注文が必要","path":"household.food.purchase_required","type":"tri"},
    {"group":"家の運営","id":"food_missing_items","label":"食事に必要な不足品がある","path":"household.food.missing_items","type":"tri"},
    {"group":"外出・天候","id":"outing_transport_context","label":"移動手段・所要時間を具体的に確認できる","path":"context.outing.transport_context_available","type":"tri"},
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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

    source_paths = [Path(args.template),Path(args.css),Path(args.js),Path(args.catalog),Path(args.rules),Path(args.bundles),Path(args.review),Path(args.boundaries),Path(args.registry),Path(args.intake)]
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

    digest=hashlib.sha256()
    for path in source_paths:
        digest.update(path.as_posix().encode());digest.update(b"\0");digest.update(path.read_bytes());digest.update(b"\0")
    digest.update(json.dumps(FIELD_ADDITIONS,ensure_ascii=False,sort_keys=True).encode())
    build_id=digest.hexdigest()

    embedded={
        "build":{"id":build_id,"schema_version":2,"catalog_items":len(catalog),"rules":len(rules.get("rules",[])),"raw_state_fields":registry.get("field_count"),"privacy_default":"local_only","network_runtime":"blocked_by_csp","console_field_additions":len(FIELD_ADDITIONS)},
        "catalog":catalog,"rules":rules,"bundles":bundles,"review":review,"boundaries":boundaries,"registry":registry,"intakeSpec":intake,"consoleFieldAdditions":FIELD_ADDITIONS
    }

    js=Path(args.js).read_text(encoding="utf-8")
    marker="const QUICK_FIELDS = ["
    if marker not in js:
        raise SystemExit("shadow console JS marker not found")
    js=js.replace(marker,"const QUICK_FIELDS = [...(DATA.consoleFieldAdditions || []),",1)

    html=Path(args.template).read_text(encoding="utf-8")
    html=html.replace("__SHADOW_CSS__",Path(args.css).read_text(encoding="utf-8"))
    html=html.replace("__EMBEDDED_DATA__",safe_inline_json(embedded))
    html=html.replace("__SHADOW_JS__",js)
    if any(token in html for token in ("__SHADOW_CSS__","__EMBEDDED_DATA__","__SHADOW_JS__")):
        raise SystemExit("shadow-console template replacement incomplete")

    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(html,encoding="utf-8")
    print(json.dumps({"output":str(out),"bytes":out.stat().st_size,"build_id":build_id,"catalog_items":len(catalog),"rules":len(rules.get("rules",[])),"single_file":True,"field_additions":len(FIELD_ADDITIONS)},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
