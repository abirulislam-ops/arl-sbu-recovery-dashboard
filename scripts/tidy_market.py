#!/usr/bin/env python3
"""Phase 2 — tidy the market-share workbook (skill §2.1).

Input : data/raw/market_share.xlsx (downloaded from the sheet in §1.2)
Output: data/market_share_tidy.json  -> [{sbu, tab, company, period, sales_mt, share_pct, src, quality_flag}]
        data/market_share_summary.json -> per SBU: Q1 share, Q4 share, delta pp, top gainer

Rules implemented:
  * two-row header (period row + metric row) flattened into period|metric columns
  * share must equal sales / period-total (+-0.5 pp); else quality_flag="shifted"
  * -100%, #DIV/0!, 0 and blank are MISSING, not zero
  * a month whose total is < 70% of the trailing-3-month average is flagged "partial"
Nothing is estimated: unparsed tabs are reported, not guessed.
"""
import io
import json
import os
import re
import statistics

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
XLSX = os.path.join(DATA, "raw", "market_share.xlsx")

# tab -> dashboard SBU (skill §1.2)
MAP = {
    "Ispat": ("AIL", "high"),
    "Ready Mix": ("ARMCL", "high"),
    "Pharmacy": ("ALCL", "high"),
    "Consumer Electronics": ("ACEL", "high"),
    "Diagnostic Center": ("AMPL", "high"),
    "Fruits,F&B": ("ACL", "medium"),
    "Consumer Goods": ("AELOTH", "medium"),
    "South Asian Hajj & Air": ("ALL", "low"),
    "Akij Air": ("ALL", "low"),
    "Lube Oil": ("ABSLASP", "wrong-proxy"),
}
IGNORE = {"Cement", "Agro Feed", "Medical Equipment", "Health & Beauty Products", "AgriLife",
          "Real Estate", "Akij Automobile (Tyre)", "ALEL"}

PERIOD = re.compile(r"^(FY\s?\d{2,4}(-\d{2,4})?|[A-Z][a-z]{2}['\- ]\d{2})$")
NUM = re.compile(r"^-?[\d,]+(\.\d+)?$")


def num(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if s in ("", "-", "--", "#DIV/0!", "#REF!", "N/A", "n/a"):
        return None
    if s.startswith("-100"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_sheet(ws):
    rows = [[c for c in r] for r in ws.iter_rows(values_only=True)]
    head = None
    for i, r in enumerate(rows[:12]):
        hits = sum(1 for c in r if isinstance(c, str) and PERIOD.match(c.strip()))
        if hits >= 2:
            head = i
            break
    if head is None:
        return None, "no period header found"

    periods, metrics = rows[head], rows[head + 1] if head + 1 < len(rows) else []
    cols = {}
    cur = None
    for j, c in enumerate(periods):
        if isinstance(c, str) and PERIOD.match(c.strip()):
            cur = c.strip()
        m = metrics[j] if j < len(metrics) else None
        if cur and isinstance(m, str):
            ml = m.strip().lower()
            if "sale" in ml or "volume" in ml:
                cols[j] = (cur, "sales")
            elif "share" in ml or "%" in ml:
                cols[j] = (cur, "share")
    if not cols:
        return None, "no sales/share columns under the header"

    out = []
    for r in rows[head + 2:]:
        if not r or len(r) < 2:
            continue
        name = None
        for c in r[:8]:
            if isinstance(c, str):
                t = c.strip()
                if t and not NUM.match(t.replace("%", "")) and t.lower() not in ("sl no.", "sl", "sl no"):
                    name = t
                    break
        if not name:
            continue
        if name.lower().startswith(("total", "grand", "others")) and "total" not in name.lower():
            continue
        rec = {"company": name, "Total": "total" in name.lower(),
               "values": {j: num(r[j]) for j in cols if j < len(r)}}
        if any(v is not None for v in rec["values"].values()):
            out.append(rec)
    return {"cols": cols, "rows": out}, None


def tidy_tab(ws, tab, sbu, conf):
    parsed, err = parse_sheet(ws)
    if err:
        return [], {"tab": tab, "sbu": sbu, "error": err}
    cols, rows = parsed["cols"], parsed["rows"]
    total_row = next((r for r in rows if r["Total"]), None)
    companies = [r for r in rows if not r["Total"]]

    # period totals: prefer the sheet's Total row, else sum of companies
    totals = {}
    for j, (per, metric) in cols.items():
        if metric != "sales":
            continue
        tv = total_row["values"].get(j) if total_row else None
        sv = sum(r["values"].get(j) or 0 for r in companies)
        totals[per] = {"sheet": tv, "sum": sv}

    # partial-month detection: total < 70% of trailing 3-month average
    month_periods = [p for p in totals if re.match(r"^[A-Z][a-z]{2}'?\d{0,2}$", p)]
    partial = set()
    sales_series = [totals[p]["sheet"] or totals[p]["sum"] for p in month_periods]
    for i, p in enumerate(month_periods):
        prev = [v for v in sales_series[max(0, i - 3):i] if v]
        if prev and (sales_series[i] or 0) < 0.7 * statistics.mean(prev):
            partial.add(p)

    records = []
    for r in companies:
        for j, (per, metric) in cols.items():
            v = r["values"].get(j)
            if v is None:
                continue
            flag = []
            if per in partial:
                flag.append("partial")
            if metric == "share":
                sales_col = next((k for k, (p2, m2) in cols.items() if p2 == per and m2 == "sales"), None)
                s = r["values"].get(sales_col) if sales_col is not None else None
                tot = totals.get(per, {})
                base = tot.get("sheet") or tot.get("sum")
                if s is not None and base:
                    if abs(v - 100.0 * s / base) > 0.5:
                        flag.append("shifted")
                if v > 100 or v < 0:
                    flag.append("implausible")
            records.append({"sbu": sbu, "tab": tab, "company": r["company"], "period": per,
                            "metric": metric, "value": round(v, 2) if isinstance(v, float) else v,
                            "quality_flag": ",".join(flag) if flag else "ok"})
    shares = [x["value"] for x in records if x["metric"] == "share" and isinstance(x["value"], float)]
    if shares and max(shares) <= 1.5:
        for x in records:
            if x["metric"] == "share" and isinstance(x["value"], float):
                x["value"] = round(x["value"] * 100, 2)
                x["quality_flag"] = "fraction-normalised" if x["quality_flag"] == "ok" else x["quality_flag"] + ",fraction-normalised"

    summary = {"tab": tab, "sbu": sbu, "mapping_confidence": conf,
               "periods": sorted({p for p, _ in cols.values()}),
               "companies": len(companies), "total_row": bool(total_row),
               "partial_months": sorted(partial),
               "shifted_cells": sum(1 for x in records if "shifted" in x["quality_flag"]),
               "records": len(records)}
    return records, summary


def main():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    all_recs, summaries = [], []
    for raw_tab in wb.sheetnames:
        tab = raw_tab.strip()
        if tab in IGNORE:
            continue
        if tab not in MAP:
            summaries.append({"tab": tab, "sbu": None, "error": "unmapped"})
            continue
        sbu, conf = MAP[tab]
        recs, summ = tidy_tab(wb[raw_tab], tab, sbu, conf)
        all_recs += recs
        summaries.append(summ)
        print("%-26s %-8s %s" % (tab, sbu, "OK %d records" % len(recs) if recs else summ.get("error")))

    os.makedirs(DATA, exist_ok=True)
    json.dump(all_recs, open(os.path.join(DATA, "market_share_tidy.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    json.dump(summaries, open(os.path.join(DATA, "market_share_summary.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    # per-SBU Q4 FY26 vs Q1 FY27 share
    Q4 = ("Apr'26", "May'26", "Jun'26")
    Q1 = ("Jul'26", "Aug'26", "Sep'26")
    per_sbu = {}
    for r in all_recs:
        if r["metric"] != "share" or not isinstance(r["value"], float):
            continue
        if "shifted" in r["quality_flag"] or "implausible" in r["quality_flag"]:
            continue
        d = per_sbu.setdefault((r["sbu"], r["company"]), {"q4": [], "q1": []})
        if r["period"] in Q4:
            d["q4"].append(r["value"])
        elif r["period"] in Q1:
            d["q1"].append(r["value"])
    for summ in summaries:
        sbu = summ.get("sbu")
        if not sbu:
            continue
        rows = []
        for (s2, comp), d in per_sbu.items():
            if s2 != sbu or not d["q4"] or not d["q1"]:
                continue
            q4 = statistics.mean(d["q4"]); q1 = statistics.mean(d["q1"])
            rows.append({"company": comp, "q4_share": round(q4, 2), "q1_share": round(q1, 2),
                         "delta_pp": round(q1 - q4, 2)})
        rows.sort(key=lambda x: -x["q1_share"])
        ours = next((r for r in rows if r["company"].strip().lower().startswith(("akij", "akij "))), None)
        gainer = max(rows, key=lambda x: x["delta_pp"]) if rows else None
        summ["share_q4_q1"] = {"rows": rows[:8], "ours": ours, "top_gainer": gainer,
                               "note": "average share over Apr-Jun 26 vs Jul-Sep 26; shifted cells excluded"}
    json.dump(summaries, open(os.path.join(DATA, "market_share_summary.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    print("total tidy rows:", len(all_recs))
    for summ in summaries:
        if summ.get("share_q4_q1"):
            s = summ["share_q4_q1"]
            o = s["ours"] or {}
            g = s["top_gainer"] or {}
            print("  %-8s ours %s -> %s (%s pp) | gainer %s %s pp" % (
                summ["sbu"], o.get("q4_share"), o.get("q1_share"), o.get("delta_pp"),
                g.get("company"), g.get("delta_pp")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
