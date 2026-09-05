#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_full_day import evaluate, read_jsonl

OBS_HEADERS = [
    "date","responsibility_id","actual_label","engine_surfaced","engine_layer",
    "actually_needed","timing","partner_prompted","loop_closed","master_gap",
    "evidence_overclaim","notes"
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require_local_contract(payload, label):
    if not (payload.get("private") is True or payload.get("synthetic") is True):
        raise SystemExit(f"{label} must declare private=true or synthetic=true")


def write_review(path: Path, result: dict):
    layer_ja = {"now":"今見る","today":"今日の候補","routine":"ルーティン","review":"レビュー"}
    out = [
        "# 夜の照合用 — engine candidates",
        "",
        "このファイルはshadow testの夜まで開かない。候補は生活判断の正解ではない。",
        "",
        f"Date: `{result.get('date')}`",
        "",
        "| 層 | 件数 |",
        "|---|---:|"
    ]
    for layer in ("now","today","routine","review"):
        out.append(f"| {layer_ja[layer]} | {result['counts'].get(layer,0)} |")
    out.append("")
    for layer in ("now","today","routine","review"):
        items = [x for x in result["candidates"] if x["layer"] == layer]
        out.extend([f"## {layer_ja[layer]} — {len(items)}件",""])
        if not items:
            out.extend(["該当なし。",""])
            continue
        out.extend(["| ID | 項目 | 反応した状態 | 閉じる条件 |","|---|---|---|---|"])
        for x in items:
            out.append(f"| `{x['id']}` | {x['label']} | {', '.join(x['matched_signals'])} | {x['close_condition']} |")
        out.append("")
    path.write_text("\n".join(out)+"\n",encoding="utf-8")


def write_observation_csv(path: Path, result: dict):
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=OBS_HEADERS)
        w.writeheader()
        for x in result["candidates"]:
            w.writerow({
                "date":result.get("date", ""),
                "responsibility_id":x["id"],
                "actual_label":x["label"],
                "engine_surfaced":"yes",
                "engine_layer":x["layer"],
                "actually_needed":"",
                "timing":"",
                "partner_prompted":"no",
                "loop_closed":"",
                "master_gap":"no",
                "evidence_overclaim":"no",
                "notes":""
            })
        for _ in range(12):
            w.writerow({"date":result.get("date", ""),"engine_surfaced":"no"})


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--profile",required=True)
    ap.add_argument("--day-state",required=True)
    ap.add_argument("--rules",default="artifacts/full_activation_rules_v1.jsonl")
    ap.add_argument("--out-dir",default=None)
    args=ap.parse_args()

    profile_payload=load_json(Path(args.profile))
    day_payload=load_json(Path(args.day_state))
    require_local_contract(profile_payload,"profile")
    require_local_contract(day_payload,"day-state")
    day={"date":day_payload["date"],"profile":profile_payload["profile"],"signals":day_payload.get("signals",{})}
    rules=read_jsonl(Path(args.rules))
    result=evaluate(rules,day)

    out_dir=Path(args.out_dir or f"artifacts/private_shadow/{day['date']}")
    out_dir.mkdir(parents=True,exist_ok=True)
    candidates_path=out_dir/"engine_candidates.json"
    review_path=out_dir/"engine_candidates_night_review.md"
    csv_path=out_dir/"night_observations_template.csv"
    candidates_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    write_review(review_path,result)
    write_observation_csv(csv_path,result)
    manifest={
        "schema_version":1,
        "mode":"shadow_only_not_active_reliance",
        "date":day["date"],
        "profile_id":profile_payload.get("profile_id"),
        "candidate_counts":result["counts"],
        "files":{}
    }
    for p in (candidates_path,review_path,csv_path):
        manifest["files"][p.name]={"sha256":sha256(p),"bytes":p.stat().st_size}
    (out_dir/"packet_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"out_dir":str(out_dir),"counts":result["counts"]},ensure_ascii=False))

if __name__=="__main__":
    main()
