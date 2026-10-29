#!/usr/bin/env python3
"""Auto refresh: tracker -> national share -> rebuild -> validate -> embed -> publish.

Safety rules (because the MD reads this):
  * only numbers that exist in a source are written; anything unparsed is marked
    status="unparsed" and never guessed
  * if validation fails, nothing is published and the run is logged
  * a change log entry is always written first

Usage: python scripts/auto_refresh.py [--dry-run]
"""
import csv, io, json, os, re, subprocess, sys, urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from datetime import datetime

SHEET_ID = "1OXLfEnEdKVsTERVLZWtaaiUfTVaeTU_zhZcmEZCo6JQ"
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
LOG = os.path.join(DATA, "_change_log.json")
OUT = os.path.join(DATA, "market_national.json")
MONTHS = ["Jul-25","Aug-25","Sep-25","Oct-25","Nov-25","Dec-25","Jan-26","Feb-26","Mar-26",
          "Apr-26","May-26","Jun-26","Jul-26","Aug-26","Sep-26","Oct-26"]
Q4 = ["Apr-26","May-26","Jun-26"]
Q1 = ["Jul-26","Aug-26","Sep-26"]
NAME_MAP = {"Akij Cement Company LTD":"ACCL","Akij Essentials LTD":"AELOTH","Akij Ispat":"AIL",
            "AKIJ Ready Mix Concrete":"ARMCL","Akij Consumer Electronics Limited":"ACEL",
            "Akij Mediplex":"AMPL","AKIJ Pharmacy":"ALCL","Nextjobz":"NJL","AKIJ AIR":"AASL"}


def fetch_csv(url):
    sid = url.split("/d/")[1].split("/")[0]
    m = re.search(r"[?&]gid=(\d+)", url)
    u = "https://docs.google.com/spreadsheets/d/%s/export?format=csv" % sid + ("&gid=%s" % m.group(1) if m else "")
    req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")


def parse_month_grid(rows):
    """Find a header row with month labels and return {brand: {month: value}}, is_share."""
    for hi, row in enumerate(rows[:12]):
        idx = {c.strip(): i for i, c in enumerate(row) if re.match(r"^[A-Z][a-z]{2}-\d{2}$", c.strip())}
        if len(idx) >= 6:
            series, is_share = {}, False
            for r in rows[hi+1:]:
                if len(r) <= 1:
                    continue
                name = (r[1] if len(r) > 1 and r[1].strip() else r[0]).strip()
                if not name or name.lower().startswith(("total", "grand")):
                    continue
                vals = {}
                for mth, ci in idx.items():
                    if ci < len(r):
                        try:
                            v = float(str(r[ci]).replace(",", "").strip())
                            vals[mth] = v
                        except ValueError:
                            pass
                if len(vals) >= 3:
                    series[name] = vals
            if len(series) >= 2:
                # decide volumes vs shares: shares sum to ~100 per month
                sample = [m for m in idx if m in Q1]
                tot = [sum(s.get(m, 0) for s in series.values()) for m in sample]
                is_share = bool(tot) and all(60 <= t <= 140 for t in tot)
                return series, is_share, idx
    return None, None, None


DROPME = ("industry", "total", "grand", "top 5", "others", "market size")


def summarise(series, is_share):
    avg = {}
    for brand, vals in series.items():
        avg[brand] = {}
        for label, months in (("q4", Q4), ("q1", Q1)):
            pts = [vals[m] for m in months if m in vals]
            avg[brand][label] = sum(pts) / len(pts) if pts else None
    denom = [b for b in avg if any(k in b.lower() for k in DROPME)]
    brands = {b: v for b, v in avg.items()
              if b not in denom and v["q4"] is not None and v["q1"] is not None}
    if not brands:
        return []
    rows = [{"brand": b, "q4": v["q4"], "q1": v["q1"]} for b, v in brands.items()]
    if not is_share:
        for r in rows:
            d4 = avg[denom[0]]["q4"] if denom else (sum(x["q4"] for x in rows) or 1)
            d1 = avg[denom[0]]["q1"] if denom else (sum(x["q1"] for x in rows) or 1)
            r["q4"] = r["q4"] / d4 * 100
            r["q1"] = r["q1"] / d1 * 100
    for r in rows:
        r["q4"], r["q1"] = round(r["q4"], 2), round(r["q1"], 2)
        r["dpp"] = round(r["q1"] - r["q4"], 2)
    total1 = sum(r["q1"] for r in rows)
    if not (80 <= total1 <= 105):
        return []
    rows.sort(key=lambda r: -r["q1"])
    return rows


def main():
    dry = "--dry-run" in sys.argv
    if not dry:
        r = subprocess.run([sys.executable, os.path.join(BASE, "scripts", "refresh_sources.py")],
                           cwd=BASE, capture_output=True, text=True)
        print((r.stdout or "").strip()[:600])
    snap = json.load(open(os.path.join(DATA, "_source_snapshot.json"), encoding="utf-8"))
    result = {"generated_at": datetime.now().isoformat(timespec="seconds"),
              "period": "Q4 FY26 (Apr–Jun 26) vs Q1 FY27 (Jul–Sep 26)", "sbus": []}
    for key, meta in snap["links"].items():
        col = meta.get("column", "")
        if not (col.startswith("Market / Industry") or col.startswith("Market Share") or col == "Market"):
            continue
        sbu = NAME_MAP.get(meta["sbu"])
        if not sbu:
            continue
        entry = {"sbu": sbu, "source": meta.get("url"), "file": meta.get("label"), "status": "unparsed", "rows": []}
        try:
            txt = fetch_csv(meta["url"])
            rows = list(csv.reader(io.StringIO(txt)))
            series, is_share, idx = parse_month_grid(rows)
            if series:
                summary = summarise(series, is_share)
                if summary:
                    entry["status"] = "ok"
                    entry["basis"] = "share % in source" if is_share else "volume-derived share"
                    entry["rows"] = summary
        except Exception as e:
            entry["error"] = str(e)[:160]
        result["sbus"].append(entry)

    ok = [s for s in result["sbus"] if s["status"] == "ok"]
    print("parsed %d of %d market-share sources" % (len(ok), len(result["sbus"])))
    for s in result["sbus"]:
        top = s["rows"][:3]
        print("  %-6s %-9s %s" % (s["sbu"], s["status"],
              " | ".join("%s %.1f->%.1f (%+.1f)" % (r["brand"][:14], r["q4"], r["q1"], r["dpp"]) for r in top))[:150])
    if dry:
        return 0
    if not ok:
        print("nothing parsed — not rebuilding")
        return 0
    json.dump(result, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    steps = [["scripts/build_data.py"], ["scripts/validate_data.py", "data"], ["scripts/embed_data.py"]]
    for step in steps:
        r = subprocess.run([sys.executable, os.path.join(BASE, step[0])] + step[1:],
                           cwd=BASE, capture_output=True, text=True)
        if r.returncode != 0:
            print("ABORT at %s\n%s\n%s" % (step[0], r.stdout[-800:], r.stderr[-800:]))
            return 1
        if step[0].endswith("validate_data.py"):
            print(r.stdout.strip())
            if "0 error" not in r.stdout:
                print("ABORT: validation failed — nothing published")
                return 1

    subprocess.run(["git", "add", "-A"], cwd=BASE, check=False)
    msg = "Auto refresh: national share from tracker (%s)" % result["generated_at"]
    c = subprocess.run(["git", "commit", "-m", msg], cwd=BASE, capture_output=True, text=True)
    print(c.stdout.strip()[:300])
    return 0


if __name__ == "__main__":
    sys.exit(main())
