#!/usr/bin/env python3
"""Embed the JSON snapshots into index.html between the MDDATA markers.

The site is a single static HTML file; Vercel cannot call MCP at runtime, so the
validated snapshots are inlined. data/*.json stays the source of truth:
    python scripts/build_data.py && python scripts/validate_data.py data/
    python scripts/embed_data.py
"""
import json, os, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
HTML = os.path.join(BASE, "index.html")

FILES = {
    "pnl": "sbu_pnl.json",
    "dir": "sbu_direction.json",
    "decisions": "decisions.json",
    "hyp": "hypotheses.json",
    "market": "market_share.json",
    "leadership": "market_leadership.json",
    "diagnosis": "market_diagnosis.json",
    "se": "se_commitment.json",
    "churn": "dealer_churn.json",
    "trend": "dealer_trend.json",
    "recovery": "recovery.json",
    "insights": "insights.json",
    "health": "customer_health.json",
    "crm": "crm.json",
    "national": "market_national.json",
    "links": "source_links.json",
    "regional": "regional_logistics.json",
    "context": "market_context.json",
    "people": "people.json",
    "seven_p": "seven_p.json",
    "bcg": "bcg.json",
    "brand_audit": "brand_audit.json",
    "campaigns": "campaigns.json",
    "lineage": "_lineage.json",
}


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def parse_source_map():
    p = os.path.join(DATA, "_source_map.md")
    rows = []
    if not os.path.exists(p):
        return rows
    for line in open(p, encoding="utf-8"):
        m = re.match(r"^\|\s*([A-I]\d)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", line.strip())
        if m:
            rows.append({"id": m.group(1).strip(), "item": m.group(2).strip(),
                         "source": m.group(3).strip(), "status": m.group(4).strip(),
                         "owner": m.group(5).strip(), "fresh": m.group(6).strip()})
    return rows


def main():
    md = {k: load(v) for k, v in FILES.items()}
    lineage = md.pop("lineage", {})
    md["as_of"] = lineage.get("as_of", "")
    md["generated_at"] = lineage.get("generated_at", "")
    md["pending"] = lineage.get("pending", {})
    md["source_map"] = parse_source_map()

    payload = json.dumps(md, ensure_ascii=False, separators=(",", ":"))
    html = open(HTML, encoding="utf-8").read()
    if "/*<<MDDATA>>*/" not in html:
        raise SystemExit("MDDATA markers not found in index.html")
    new = re.sub(r"/\*<<MDDATA>>\*/.*?/\*<</MDDATA>>\*/",
                 "/*<<MDDATA>>*/\nconst MD=" + payload + ";\n/*<</MDDATA>>*/",
                 html, flags=re.S)
    open(HTML, "w", encoding="utf-8").write(new)
    print("embedded %d bytes of data into index.html" % len(payload))


if __name__ == "__main__":
    main()




