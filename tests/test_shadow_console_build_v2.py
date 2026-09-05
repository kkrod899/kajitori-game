#!/usr/bin/env python3
import json
import re
from pathlib import Path

html_path = Path("artifacts/shadow_console_v2.html")
assert html_path.exists()
html = html_path.read_text(encoding="utf-8")
js = Path("experiments/shadow-console-v2/shadow.js").read_text(encoding="utf-8")

assert "__SHADOW_CSS__" not in html
assert "__EMBEDDED_DATA__" not in html
assert "__SHADOW_JS__" not in html
assert "default-src 'none'" in html
assert "connect-src 'none'" in html
assert "kajitori_shadow_v2" in html
assert "判断には使わない" in html
assert "候補を生成して封印" in html
assert "actual_atomic" in html
assert "surfaced_card" in html
assert "fixed_target_count" not in html

# The generated console is a single runtime file: no external scripts, stylesheets or images.
assert not re.search(r'<script[^>]+src=', html, re.I)
assert not re.search(r'<link[^>]+rel=["\']stylesheet', html, re.I)
assert not re.search(r'<img[^>]+src=["\']https?://', html, re.I)

# Runtime privacy contract: the console source cannot call external networking APIs.
for banned in ("fetch(", "XMLHttpRequest", "WebSocket(", "EventSource(", "sendBeacon("):
    assert banned not in js, banned
assert "localStorage" in js
assert "serviceWorker" not in js

m = re.search(r'window\.__SHADOW_DATA__=(.*?);</script>', html, re.S)
assert m, "embedded data payload missing"
embedded = json.loads(m.group(1).replace("<\\/", "</"))
assert embedded["build"]["catalog_items"] == 294
assert embedded["build"]["rules"] == len(embedded["rules"]["rules"])
assert embedded["build"]["privacy_default"] == "local_only"
assert embedded["build"]["network_runtime"] == "blocked_by_csp"
assert embedded["build"]["console_field_additions"] >= 6
assert len(embedded["review"]["items"]) == 43
assert not any(x["status"] not in {"PASS_DIRECT", "PASS_WITH_BOUNDARY"} for x in embedded["review"]["items"])

print("shadow console v2 build validation: PASS")
print(f"bytes={html_path.stat().st_size} catalog={embedded['build']['catalog_items']} rules={embedded['build']['rules']}")
