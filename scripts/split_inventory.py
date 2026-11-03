#!/usr/bin/env python3
"""Phase 1 inventory: split the single-file dashboard into a working tree.

  src/app.js           the inline <script> verbatim (read-only copy)
  src/data/md.json     every MD.* block as JSON
  src/data/inventory.json  block sizes, page list, function list

Nothing here is loaded by index.html; it exists so later phases can work on
separate files and rebuild the single HTML deterministically.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(BASE, "index.html")
SRC = os.path.join(BASE, "src")
DATA = os.path.join(SRC, "data")

html = open(HTML, encoding="utf-8-sig").read()

# 1. the single inline script
m = re.search(r"<script>(.*)</script>", html, re.S)
script = m.group(1) if m else ""
os.makedirs(DATA, exist_ok=True)
open(os.path.join(SRC, "app.js"), "w", encoding="utf-8", newline="").write(script)

# 2. MD block
i = html.find("const MD=")
start = html.find("{", i)
depth, j, in_str, esc = 0, start, False, False
while j < len(html):
    ch = html[j]
    if in_str:
        if esc:
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == '"':
            in_str = False
    else:
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
    j += 1
md = json.loads(html[start:j + 1])
open(os.path.join(DATA, "md.json"), "w", encoding="utf-8").write(json.dumps(md, indent=1, ensure_ascii=False))

# 3. inventory
pages = re.findall(r'id="pane-([a-z0-9\-]+)"', html)
functions = sorted(set(re.findall(r"function\s+([A-Za-z_$][\w$]*)\s*\(", script)))
consts = sorted(set(re.findall(r"const\s+([A-Z][A-Z0-9_]{1,20})\s*=", script)))
inv = {
    "html_bytes": len(html),
    "script_bytes": len(script),
    "pages": pages,
    "sbU_panes": [p for p in pages if p.startswith("sbu-")],
    "functions": functions,
    "consts": consts,
    "md_blocks": {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in md.items()},
    "md_bytes": len(json.dumps(md, ensure_ascii=False)),
}
open(os.path.join(DATA, "inventory.json"), "w", encoding="utf-8").write(json.dumps(inv, indent=1, ensure_ascii=False))

print("html %.0f KB | script %.0f KB | MD %.0f KB" % (len(html) / 1024, len(script) / 1024, inv["md_bytes"] / 1024))
print("pages:", ", ".join(pages))
print("SBU panes:", len(inv["sbU_panes"]))
print("MD blocks:", len(md))
print("consts:", ", ".join(consts[:14]))
print("functions:", len(functions))
