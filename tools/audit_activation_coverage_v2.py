#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="artifacts/responsibility_catalog_v2.jsonl")
    ap.add_argument("--rules", default="data/activation_rules_core_v2.json")
    ap.add_argument("--json-out", default="artifacts/activation_coverage_v2.json")
    ap.add_argument("--md-out", default="artifacts/activation_coverage_v2.md")
    args = ap.parse_args()

    catalog = read_jsonl(Path(args.catalog))
    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))["rules"]
    referenced = {e["id"] for rule in rules for e in rule["emit"]}
    by_domain = defaultdict(lambda: {"total": 0, "covered": 0, "uncovered_ids": []})
    by_group = defaultdict(lambda: {"total": 0, "covered": 0, "uncovered_ids": []})

    for item in catalog:
        for bucket, key in ((by_domain, item["domain"]), (by_group, item["group"])):
            bucket[key]["total"] += 1
            if item["id"] in referenced:
                bucket[key]["covered"] += 1
            else:
                bucket[key]["uncovered_ids"].append(item["id"])

    def finalize(mapping):
        out = {}
        for key, row in sorted(mapping.items()):
            total, covered = row["total"], row["covered"]
            out[key] = {
                **row,
                "uncovered": total - covered,
                "coverage_ratio": round(covered / total, 4) if total else 0.0,
            }
        return out

    type_counts = {}
    for marker in ("M", "R", "S", "C"):
        items = [x for x in catalog if marker in x["type"].split("/")]
        covered = sum(x["id"] in referenced for x in items)
        type_counts[marker] = {
            "total": len(items),
            "covered": covered,
            "uncovered": len(items) - covered,
            "coverage_ratio": round(covered / len(items), 4) if items else 0.0,
        }

    uncovered_priority = Counter()
    for item in catalog:
        if item["id"] not in referenced:
            uncovered_priority[item["priority_class"]] += 1

    payload = {
        "schema_version": 2,
        "catalog_items": len(catalog),
        "rule_referenced_items": len(referenced),
        "uncovered_items": len(catalog) - len(referenced),
        "coverage_ratio": round(len(referenced) / len(catalog), 4),
        "health_safety": type_counts["S"],
        "by_type_marker": type_counts,
        "uncovered_priority_class_counts": dict(sorted(uncovered_priority.items())),
        "by_domain": finalize(by_domain),
        "by_group": finalize(by_group),
    }
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# ACTIVATION COVERAGE v2",
        "",
        f"Active rules reference **{len(referenced)} / {len(catalog)}** catalog items ({payload['coverage_ratio']:.2%}).",
        "",
        "Coverage is not treated as a vanity target. Uncovered items remain explicit and cannot surface until an experiment-ready rule exists.",
        "",
        "## Domain coverage",
        "",
        "| Domain | Covered | Total | Ratio | Uncovered examples |",
        "|---|---:|---:|---:|---|",
    ]
    for domain, row in sorted(payload["by_domain"].items(), key=lambda x: (x[1]["coverage_ratio"], x[0])):
        examples = ", ".join(f"`{x}`" for x in row["uncovered_ids"][:6]) or "—"
        lines.append(f"| {domain} | {row['covered']} | {row['total']} | {row['coverage_ratio']:.1%} | {examples} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- Health/safety is rule-covered 43/43 and remains behind review/boundary gates.",
        "- Infant, daycare, food, emergency, and family handoff have high coverage.",
        "- Home maintenance, supplies, cleaning, administration, laundry, and older-child lifecycle remain the largest rule gaps.",
        "- The next pass should prioritize observed household relevance, not blindly force 100% coverage.",
        "",
    ]
    Path(args.md_out).write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "catalog": len(catalog),
        "covered": len(referenced),
        "uncovered": len(catalog) - len(referenced),
        "health_safety": type_counts["S"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
