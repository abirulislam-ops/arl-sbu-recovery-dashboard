#!/usr/bin/env python3
"""Phase 1 audit — SBU Loss Recovery dashboard.

Reads the single-file dashboard, extracts the MD data block, recomputes every
derived metric from first principles (skill §2 rule 4) and compares it with what
the dashboard stores. Writes data/audit_report.md and prints a summary.

Read-only: nothing in index.html is modified.
"""
import csv
import io
import json
import os
import re
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
HTML = os.path.join(BASE, "index.html")
RAW = os.path.join(DATA, "raw")
SHEET = "1W-Y6vGGhxNjtOYRB_F72pNGHRV2n9MYPcElwewfLw0U"
MARKET_SHEET = "1DIO4tXgaimF9jr6W1_--zJAasGDGE5Pi"


def read_html():
    with open(HTML, encoding="utf-8-sig") as f:
        return f.read()


def extract_md(html):
    i = html.find("const MD=")
    if i < 0:
        raise SystemExit("const MD= not found")
    start = html.find("{", i)
    depth, j = 0, start
    in_str, esc = False, False
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
    return json.loads(html[start:j + 1])


def scorecard():
    p = os.path.join(DATA, "_raw", "sbu_sheet.csv")
    if not os.path.exists(p):
        return {}
    rows = list(csv.reader(open(p, encoding="utf-8-sig", errors="replace")))
    out = {}
    for r in rows[7:]:
        if len(r) < 50 or not r[1].strip():
            continue
        def n(x):
            try:
                return float(str(x).replace(",", "").strip())
            except Exception:
                return None
        out[r[1].strip()] = {"name": r[2].strip(), "rev": n(r[22]), "gp_pct": n(r[26]),
                             "eat": n(r[40]), "deficit": n(r[48]), "loss": n(r[49]),
                             "commit_rev": n(r[64]) if len(r) > 64 else None}
    return out


def market_workbook():
    os.makedirs(RAW, exist_ok=True)
    p = os.path.join(DATA, "market_share.xlsx")
    if not os.path.exists(p):
        p = os.path.join(RAW, "market_share.xlsx")
        if not os.path.exists(p):
            try:
                url = "https://docs.google.com/spreadsheets/d/%s/export?format=xlsx" % MARKET_SHEET
                blob = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read()
                open(p, "wb").write(blob)
            except Exception as e:
                return None, "download failed: %s" % str(e)[:120]
    try:
        import openpyxl
        wb = openpyxl.load_workbook(p, read_only=True)
        return wb.sheetnames, None
    except Exception as e:
        return None, "open failed: %s" % str(e)[:120]


def main():
    html = read_html()
    md = extract_md(html)
    sc = scorecard()
    pnl = {r["sbu"]: r for r in md.get("pnl", [])}
    issues = []

    def add(sev, sbu, what, detail, fix):
        issues.append({"sev": sev, "sbu": sbu, "what": what, "detail": detail, "fix": fix})

    # ---- §2.4 recompute every derived metric ----
    for code, r in pnl.items():
        rev, cogs = r.get("revenue"), r.get("cogs")
        gp_stored = r.get("gross_margin")
        gp_calc = (rev - abs(cogs)) if (rev is not None and cogs is not None) else None
        gpp_stored, gpp_calc = r.get("gp_pct"), (gp_calc / rev if gp_calc is not None and rev else None)
        sd, adm = r.get("sd_cost") or 0, r.get("admin_cost") or 0
        ebitda_calc = (gp_calc - sd - adm) if gp_calc is not None else None
        ebitda_stored = r.get("ebitda")

        if gpp_stored is not None and gpp_calc is not None and abs(gpp_stored - gpp_calc) > 0.02:
            add("CRITICAL", code, "GP% stored vs recomputed",
                "stored %.1f%% vs recomputed %.1f%% (revenue %.2f, COGS %s)" % (gpp_stored * 100, gpp_calc * 100, rev, cogs),
                "re-derive from source; one canonical value (§2.3)")
        if gp_stored is None and gpp_stored is not None:
            add("HIGH", code, "gross_margin null but gp_pct set", "gp_pct %.1f%%" % (gpp_stored * 100), "compute gross_margin or null both")
        if ebitda_stored is not None and ebitda_calc is not None and abs(ebitda_stored - ebitda_calc) > 1.0:
            add("HIGH", code, "EBITDA stored vs recomputed",
                "stored %.2f vs recomputed %.2f" % (ebitda_stored, ebitda_calc), "state EBITDA definition and recompute")
        if ebitda_stored is not None and rev and rev > 0 and ebitda_stored > rev:
            add("CRITICAL", code, "EBITDA larger than revenue", "EBITDA %.2f on revenue %.2f" % (ebitda_stored, rev), "wrong unit or wrong column")

        erp = r.get("erp_revenue_q1")
        if erp is not None and rev:
            var = (erp - rev) / rev * 100
            if abs(var) > 5:
                add("HIGH", code, "Scorecard vs ERP revenue",
                    "scorecard %.2f, ERP %.2f (%.1f%%)" % (rev, erp, var), "show scorecard, flag variance (§2.3)")

        commit, deficit = r.get("commit_rev"), r.get("deficit")
        if commit is not None and deficit:
            cov = commit / deficit * 100
            if cov < 50:
                add("MEDIUM", code, "Commitment covers under half the deficit",
                    "commit %.2f vs deficit %.2f = %.0f%%" % (commit, deficit, cov), "say 'coverage X%' next to the number")

        # scorecard cross-check
        s = sc.get(code)
        if s and s.get("rev") and rev and abs(s["rev"] - rev) > 0.01:
            add("MEDIUM", code, "Dashboard revenue differs from live scorecard",
                "dashboard %.2f vs sheet %.2f" % (rev, s["rev"]), "refresh from sheet")

    # ---- commitments that are derived, not firm ----
    for code, r in pnl.items():
        if code == "AIL" and r.get("commit_rev") is None:
            add("HIGH", "AIL", "commit_rev null in MD.pnl but 62.7 Cr used elsewhere",
                "62.7 Cr is derived (7,052 MT x 89,000/t)", "tag as assumption, or set null and show derived badge")

    # ---- §3 duplication, size, badges ----
    def count_occurrences(num):
        if num is None:
            return 0
        return html.count("%.2f" % num)

    worst = sorted(pnl.items(), key=lambda kv: -(kv[1].get("loss") or 0))[:3]
    dup_rows = [(c, r.get("loss"), count_occurrences(r.get("loss"))) for c, r in worst]
    for c, loss, n in dup_rows:
        if n >= 6:
            add("LOW", c, "Same loss figure repeated on the page", "%.2f appears %d times" % (loss, n), "show once, link elsewhere")

    for key in ("links", "leadership"):
        size = len(json.dumps(md.get(key, []), ensure_ascii=False))
        if size > 20000:
            add("MEDIUM", "-", "%s block is bookkeeping, not MD content" % key,
                "%.0f KB of the payload" % (size / 1024), "move to Data appendix (§3)")

    html_has_badge = ("covBadge" in html and "_lineage" in html) or True
    # static fetch check: are the header badges server-side?
    m = re.search(r'id="covBadge"[^>]*>([^<]*)<', html)
    badge = m.group(1).strip() if m else None
    if badge in ("", "—", "-"):
        add("MEDIUM", "-", "Header badge empty in static HTML", "covBadge renders '%s' until JS runs" % badge,
            "render it server-side or accept (documented)")

    # ---- market share workbook ----
    tabs, err = market_workbook()
    if tabs is None:
        add("HIGH", "-", "Market-share workbook not available", err or "missing", "download into ./data/market_share.xlsx")
    else:
        mapping = {"Ispat": "AIL", "Ready Mix": "ARMCL", "Pharmacy": "ALCL", "Consumer Electronics": "ACEL",
                   "Diagnostic Center": "AMPL", "Fruits,F&B": "ACL", "Consumer Goods": "AELOTH/AELTRD",
                   "South Asian Hajj & Air": "ALL?", "Akij Air": "ALL?", "Lube Oil": "ABSLASP (wrong proxy)"}
        for t in tabs:
            if t not in mapping and t not in ("Cement", "Agro Feed", "Medical Equipment", "Health & Beauty Products",
                                              "AgriLife", "Real Estate", "Akij Automobile (Tyre)", "ALEL"):
                add("LOW", "-", "Unmapped workbook tab", t, "ignore or map explicitly")
        add("HIGH", "ABSLASP", "Lube Oil tab cannot stand in for Asphalt", "asphalt is bitumen, not lubricant",
            "show 'No asphalt share data' until a bitumen tab exists")

    # ---- write report ----
    os.makedirs(DATA, exist_ok=True)
    lines = ["# Phase 1 audit — SBU Loss Recovery dashboard", "",
             "Generated by `scripts/audit_phase1.py`. Read-only: index.html was not modified.", "",
             "## Structure inventory", "",
             "| block | size (KB) | records |", "|---|---:|---:|"]
    for k, v in sorted(md.items()):
        size = len(json.dumps(v, ensure_ascii=False)) / 1024.0
        n = len(v) if isinstance(v, list) else (len(v) if isinstance(v, dict) else 1)
        lines.append("| %s | %.1f | %s |" % (k, size, n))
    lines += ["", "## Findings (%d)" % len(issues), "",
              "| # | severity | SBU | issue | detail | planned fix |", "|---|---|---|---|---|---|"]
    for i, x in enumerate(issues, 1):
        lines.append("| %d | %s | %s | %s | %s | %s |" % (i, x["sev"], x["sbu"], x["what"], x["detail"].replace("|", "/"), x["fix"]))
    crit = [x for x in issues if x["sev"] == "CRITICAL"]
    lines += ["", "## Verdict", "",
              "%d critical, %d total. %s" % (len(crit), len(issues),
                                             "Do not render until the critical items are resolved or explicitly flagged on the Data page."
                                             if crit else "No critical inconsistency.")]
    open(os.path.join(DATA, "audit_report.md"), "w", encoding="utf-8").write("\n".join(lines))

    print("blocks:", len(md), "| SBUs in pnl:", len(pnl), "| issues:", len(issues),
          "| critical:", len(crit), "| workbook tabs:", len(tabs) if tabs else 0)
    for x in issues[:14]:
        print(" %-8s %-8s %s :: %s" % (x["sev"], x["sbu"], x["what"], x["detail"][:90]))
    print("report -> data/audit_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
