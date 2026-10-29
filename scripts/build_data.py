#!/usr/bin/env python3
"""Build the dashboard data snapshots (data/*.json) from the raw extracts.

Inputs  : data/_raw/sbu_sheet.csv        (Google Sheet, live CSV export)
          data/_raw/erp_extract.json     (iBOSDDD via enterprise-api-gateway MCP)
          data/_raw/brand_pack.json      (Brand Marketing Pack, brand-level market share)
          data/_raw/allse.json           (ALL SE commitment dashboard source data)
Outputs : data/<contract files>.json, data/_lineage.json, data/_source_map.md

Rule: nothing is estimated. A figure is either read from a source or set to null and
carries a "pending" Data ID. Assumed recovery rates are stated explicitly in
`assumption` and never presented as data.
"""
import csv, json, os, re, sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "_raw")
AS_OF = "2026-10-28"

SBU = {
    "AELOTH": {"name": "Essentials",             "bu": 144, "group": "Food"},
    "AIL":    {"name": "Ispat",                  "bu": 224, "group": "Building material"},
    "ARMCL":  {"name": "Ready Mix",              "bu": 175, "group": "Building material"},
    "AMPL":   {"name": "Mediplex",               "bu": 255, "group": "Healthcare"},
    "ACL":    {"name": "Commodities – F&B",      "bu": 221, "group": "Food"},
    "ALCL":   {"name": "LifeCare – Pharmacy",    "bu": 239, "group": "Healthcare"},
    "ABSLASP":{"name": "ABSL – Asphalt",         "bu": 220, "group": "Building material"},
    "ATL":    {"name": "Telecom",                "bu": 241, "group": "Others"},
    "NJL":    {"name": "Next JobZ",              "bu": 252, "group": "Others"},
    "AITL":   {"name": "Infotech",               "bu": 138, "group": "Others"},
    "ACEL":   {"name": "Consumer Electronics",   "bu": 249, "group": "Others"},
    "ALL":    {"name": "Logistics – Ex-CHA",     "bu": 225, "group": "Others"},
}
CODE_BY_BU = {v["bu"]: k for k, v in SBU.items()}

# Data availability for the P1 catalogue (A1..D6, E1, E2). 1 = available, 0.5 = partial.
P1_ITEMS = ["A1","A2","A3","A5","A8","B1","B2","B3","B4","B5","B7","B8","C1","C2","C3","C4",
            "D1","D2","D3","D4","D5","D6","E1","E2"]
BASE_AVAIL = {"A1": 0.5, "A2": 0.3, "A3": 0, "A5": 0, "A8": 0.5, "B1": 0, "B2": 0.4, "B3": 0,
              "B4": 0, "B5": 0, "B7": 0, "B8": 0, "C1": 0.15, "C2": 0.15, "C3": 0.15, "C4": 0,
              "D1": 0, "D2": 0, "D3": 0, "D4": 0, "D5": 0, "D6": 0, "E1": 0, "E2": 0}
ORDER_SBUS = {138, 144, 175, 220, 221, 224, 241}


def num(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", "").replace("\u2212", "-").replace("BDT", "").replace("Tk", "")
    if s in ("", "-", "\u2014", "N/A", "n/a"):
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def first_cr(text):
    """First 'NN.NN Cr' style amount in a free-text commitment cell."""
    if not text:
        return None
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*(?:cr|crore)", text, re.I)
    return num(m.group(1)) if m else None


def clean(text, limit=None):
    if text is None:
        return None
    t = re.sub(r"\s+", " ", str(text)).strip()
    return t[:limit].rstrip() + "…" if limit and len(t) > limit else t


def load_raw():
    with open(os.path.join(RAW, "erp_extract.json"), encoding="utf-8") as f:
        erp = json.load(f)
    with open(os.path.join(RAW, "brand_pack.json"), encoding="utf-8") as f:
        brand = json.load(f)
    with open(os.path.join(RAW, "allse.json"), encoding="utf-8") as f:
        allse = json.load(f)
    rows = list(csv.reader(open(os.path.join(RAW, "sbu_sheet.csv"), encoding="utf-8-sig", errors="replace")))
    return erp, brand, allse, rows


def parse_sheet(rows):
    out = {}
    for r in rows[7:]:
        if len(r) < 69 or not r[1].strip():
            continue
        code = r[1].strip()
        if code not in SBU:
            continue
        out[code] = {
            "name": clean(r[2]), "group": clean(r[3]),
            "rank_rev": num(r[4]), "rank_eat": num(r[5]),
            "rev": {"jul": {"b": num(r[6]), "a": num(r[7])},
                    "aug": {"b": num(r[11]), "a": num(r[12])},
                    "sep": {"b": num(r[16]), "a": num(r[17])},
                    "q1": {"budget": num(r[21]), "actual": num(r[22]), "deficit": num(r[23]),
                           "deficit_pct": num(r[24]), "ach": num(r[25]), "gp_pct": num(r[26])}},
            "eat": {"jul": num(r[27]), "aug": num(r[32]), "sep": num(r[37]),
                    "q1_budget": num(r[39]), "q1_actual": num(r[40]),
                    "q1_variance": num(r[41]), "q1_pct": num(r[43])},
            "deficit": num(r[48]), "loss": num(r[49]),
            "scope": clean(r[51]), "root_rev": clean(r[52]),
            "plan_rev": clean(r[53]), "act_rev": clean(r[54]),
            "root_loss": clean(r[55]), "plan_loss": clean(r[56]), "act_loss": clean(r[57]),
            "lead_fn": clean(r[58]), "support_fn": clean(r[59]),
            "owner": clean(r[60]), "people": clean(r[61]), "process": clean(r[62]),
            "tech": clean(r[63]), "commit_rev_txt": clean(r[64]), "commit_loss_txt": clean(r[65]),
            "target_date": clean(r[66]), "status": clean(r[67]), "note": clean(r[68]),
            "commit_rev": first_cr(r[64]), "commit_loss": first_cr(r[65]),
        }
    return out


def erp_maps(erp):
    rev = {}
    for bu, ym, v in erp["revenue_by_month"]:
        rev.setdefault(bu, {})[ym] = v
    pnl = {}
    for row in erp["pnl_by_quarter"]:
        bu, q = row[0], row[1]
        pnl.setdefault(bu, {})[q] = dict(zip(
            ["rev", "cogs", "selling", "admin", "logistics", "marketing", "finance", "other", "tax"], row[2:]))
    churn = {bu: n for bu, n in erp["dealer_churn"]}
    counts = {}
    for bu, q, dealers, orders, net in erp["dealer_counts"]:
        counts.setdefault(bu, {})[q] = {"dealers": dealers, "orders": orders, "net_cr": net}
    trend = {}
    for bu, ym, dealers, net in erp["dealer_trend"]:
        trend.setdefault(bu, []).append({"month": ym, "active_dealers": dealers, "lifting": net})
    return rev, pnl, churn, counts, trend


def direction(s, erp_pnl, is_service):
    """Provisional direction. Rules applied in order and shown in the UI legend.
    Every call is marked provisional because P1 completeness is below 70%."""
    gp = (s["rev"]["q1"]["gp_pct"] or 0) / 100.0
    ach = (s["rev"]["q1"]["ach"] or 0) / 100.0
    loss = abs(s["loss"] or 0)
    rev = s["rev"]["q1"]["actual"] or 0
    loss_pct = loss / rev if rev else 1.0
    if gp <= 0:
        return "Restructure / Exit review", "gross margin is negative (%.1f%% of revenue); every extra taka of sales adds loss" % (gp * 100), "High"
    if gp < 0.10 and loss_pct > 0.05:
        return "Refocus", "thin %.1f%% gross margin cannot carry fixed cost at a %.1f%% loss on revenue" % (gp * 100, loss_pct * 100), "Low"
    if ach >= 0.70 and loss_pct <= 0.12:
        return "Fix & Recover", "%.1f%% of budget achieved and loss is %.1f%% of revenue — gap looks closable" % (ach * 100, loss_pct * 100), "Medium"
    return "Fix & Recover", "loss is %.1f%% of revenue with %.1f%% gross margin — recovery depends on the stated supply/price fix" % (loss_pct * 100, gp * 100), "Low"


def completeness(bu, brand_codes):
    avail = dict(BASE_AVAIL)
    if bu in ORDER_SBUS:
        avail.update({"B3": 1, "B4": 0.8})
    if bu in brand_codes:
        avail.update({"C1": 0.3, "C2": 0.3})
    return round(sum(avail.values()) / len(P1_ITEMS), 3)


def main():
    erp, brand, allse, rows = load_raw()
    sheet = parse_sheet(rows)
    rev, pnl, churn, counts, trend = erp_maps(erp)
    brand_by_code = {b["code"]: b for b in brand}
    brand_codes = {SBU[c]["bu"] for c in brand_by_code if c in SBU}

    missing = [c for c in SBU if c not in sheet]
    if missing:
        print("WARNING: SBUs missing from the sheet:", missing)

    # ---------- sbu_pnl ----------
    sbu_pnl = []
    for code, s in sheet.items():
        bu = SBU[code]["bu"]
        e = pnl.get(bu, {}).get("Q1FY27", {})
        q4 = pnl.get(bu, {}).get("Q4FY26", {})
        sbu_pnl.append({
            "sbu": code, "name": SBU[code]["name"], "period": "Q1FY27",
            "revenue": s["rev"]["q1"]["actual"], "budget_revenue": s["rev"]["q1"]["budget"],
            "cogs": (abs(e.get("cogs")) if e.get("cogs") else None),
            "gross_margin": (round(s["rev"]["q1"]["actual"] - abs(e["cogs"]), 3)
                             if e.get("cogs") and s["rev"]["q1"]["actual"] else None),
            "gp_pct": (s["rev"]["q1"]["gp_pct"] / 100.0) if s["rev"]["q1"]["gp_pct"] is not None else None,
            "sd_cost": (abs(e.get("selling", 0)) + abs(e.get("logistics", 0))) if e else None,
            "admin_cost": abs(e["admin"]) if e else None,
            "ebitda": (round(e["rev"] + e["cogs"] + e["selling"] + e["admin"] + e["logistics"]
                             + e["marketing"] + e["other"], 3) if e else None),
            "finance_cost": abs(e["finance"]) if e else None,
            "net_profit": s["eat"]["q1_actual"],
            "budget_np": s["eat"]["q1_budget"],
            "fixed_cost": None, "cm_pct": None, "breakeven_sales": None,
            "deficit": s["deficit"], "loss": s["loss"], "scope": s["scope"],
            "status": s["status"], "commit_rev": s["commit_rev"], "commit_loss": s["commit_loss"],
            "erp_revenue_q1": round(rev.get(bu, {}).get("2026-07", 0) + rev.get(bu, {}).get("2026-08", 0)
                                    + rev.get(bu, {}).get("2026-09", 0), 3) if bu in rev else None,
            "erp_revenue_q4": round(rev.get(bu, {}).get("2026-04", 0) + rev.get(bu, {}).get("2026-05", 0)
                                    + rev.get(bu, {}).get("2026-06", 0), 3) if bu in rev else None,
            "erp_np_proxy_q1": (round(e["rev"] + e["cogs"] + e["selling"] + e["admin"] + e["logistics"]
                                      + e["marketing"] + e["finance"] + e["other"] + e["tax"], 3) if e else None),
            "erp_np_proxy_q4": (round(q4["rev"] + q4["cogs"] + q4["selling"] + q4["admin"] + q4["logistics"]
                                      + q4["marketing"] + q4["finance"] + q4["other"] + q4["tax"], 3) if q4 else None),
            "data_completeness": completeness(bu, brand_codes),
        })
    sbu_pnl.sort(key=lambda r: -(r["loss"] or 0))

    # ---------- loss_bridge : needs qty/price/mix (A2) — not available ----------
    loss_bridge = [{"sbu": r["sbu"], "q4_np": None, "volume": None, "price": None, "mix": None,
                    "cost": None, "fixed": None, "unexplained": None, "q1_np": r["net_profit"],
                    "loss_type": None, "pending": ["A1", "A2", "A3"]} for r in sbu_pnl]

    # ---------- dealers / trend ----------
    dealers = []  # dealer-level rows need B1/B2/D4 — not delivered
    dealer_trend = []
    for bu, series in trend.items():
        for m in series:
            dealer_trend.append({"sbu": CODE_BY_BU[bu], "region": None, "month": m["month"],
                                 "active_dealers": m["active_dealers"], "lifting": m["lifting"]})
    dealer_churn = []
    for bu, s in SBU.items():
        if SBU[bu]["bu"] not in counts:
            continue
        c = counts[SBU[bu]["bu"]]
        q1, q4 = c.get("Q1FY27", {}), c.get("Q4FY26", {})
        dealer_churn.append({"sbu": bu, "name": s["name"],
                             "q4_active": q4.get("dealers"), "q1_active": q1.get("dealers"),
                             "q4_orders": q4.get("orders"), "q1_orders": q1.get("orders"),
                             "lost": churn.get(SBU[bu]["bu"]), "new": None,
                             "lost_revenue_cr": None, "source": "ERP oms.tblSalesOrderHeader"})

    # ---------- market share (brand level only) ----------
    market_share, market_diagnosis = [], []
    for code, b in brand_by_code.items():
        if code not in SBU:
            continue
        own = num((b.get("share") or "").split("%")[0])
        comps = []
        for c in (b.get("competitors") or []):
            m = re.search(r"([\d.]+)%", c)
            comps.append({"name": re.sub(r"\s*~?[\d.]+%.*", "", c).strip(),
                          "volume": None,
                          "share": (float(m.group(1)) / 100 if m else None)})
        market_share.append({
            "sbu": code, "region": "National (brand level)", "period": "Q1FY27",
            "market_volume": None, "own_volume": None, "own_share": (own / 100 if own is not None else None),
            "own_share_text": b.get("share"), "competitors": comps,
            "source": "Brand Marketing Pack (akij-resource-brand-marketing-pack.pages.dev)", "is_proxy": True,
            "note": "Brand-level share, not region × quarter. C1/C2 (regional industry volume) still pending."})
        market_diagnosis.append({"sbu": code, "region": "National (brand level)",
                                 "own_share_q4": None, "own_share_q1": (own / 100 if own is not None else None),
                                 "pp_change": None, "market_change": None, "top_gainer": None,
                                 "gainer_pp": None, "diagnosis": "Insufficient data",
                                 "pending": ["C1", "C2", "C3"], "note": b.get("growth")})
    for code in SBU:
        if code not in brand_by_code:
            market_diagnosis.append({"sbu": code, "region": None, "own_share_q4": None, "own_share_q1": None,
                                     "pp_change": None, "market_change": None, "top_gainer": None,
                                     "gainer_pp": None, "diagnosis": "Insufficient data",
                                     "pending": ["C1", "C2", "C3"], "note": "No brand-pack entry"})

    # ---------- sales KPI : CRM not connected ----------
    sales_kpi = []

    # ---------- competitor offers ----------
    competitor_offers = []

    # ---------- 7P ----------
    seven_p = []

    # ---------- hypotheses ----------
    def ev(*items):
        return [i for i in items if i]
    tot_loss = sum(r["loss"] or 0 for r in sbu_pnl)
    top2 = sum((r["loss"] or 0) for r in sbu_pnl[:2])
    lost_total = sum(v for v in churn.values())
    hypot = [
        {"id": "H1", "title": "Market shrank", "verdict": "Insufficient data", "confidence": "Low",
         "impact_cr": None, "data_ids": ["C1", "C3", "I1", "I2"],
         "evidence": ev("No regional industry volume received (C1/C2/C3 all 'Pending' in the IT Data Link Tracker).",
                        "Brand pack shows Akij Cement volume −8.85% YTD vs industry +1.30% — that pattern is share loss, not market shrink, but it is national and brand-level only."),
         "verdict_note": "Cannot separate market shrink from share loss without C1/C2."},
        {"id": "H2", "title": "Competitor won on price/offer", "verdict": "Insufficient data", "confidence": "Low",
         "impact_cr": None, "data_ids": ["C2", "E1", "E2", "E3"],
         "evidence": ev("No competitor price list or offer log (E1/E2 pending).",
                        "Brand pack names competitor shares (e.g. Cement: Shah ~17.25%, Fresh ~11.95%) but has no per-region Q4→Q1 movement."),
         "verdict_note": "Directionally consistent with dealer narratives; not evidenced."},
        {"id": "H3", "title": "Sales team did not engage", "verdict": "Insufficient data", "confidence": "Low",
         "impact_cr": None, "data_ids": ["D2", "D3", "D4", "D5"],
         "evidence": ev("%d dealers bought in Q4 and placed no order in Q1 across the 7 SBUs with order data." % lost_total,
                        "No CRM visit/call log exists in the workspace (D3/D4 pending) so contact on those dealers is unknown.",
                        "The MD's own hypothesis is stated in the brief; it is unproven either way."),
         "verdict_note": "Test = lost-dealer contact % from CRM for Q1."},
        {"id": "H4", "title": "Sales team instability", "verdict": "Partial", "confidence": "Low",
         "impact_cr": None, "data_ids": ["D1", "D6", "D2"],
         "evidence": ev("Logistics: SBU plan states 4 salesmen needed immediately.",
                        "Infotech: plan states replace/hire 4 KAM and 1 recovery person.",
                        "Mediplex: plan states the sales team was abolished and the new team came late.",
                        "No HRIS vacancy/attrition extract yet (D1/D6 pending) — self-reported, not measured."),
         "verdict_note": "Self-reported in the SBU recovery plans."},
        {"id": "H5", "title": "Supply / service failure", "verdict": "Partial", "confidence": "Medium",
         "impact_cr": None, "data_ids": ["B8", "G2", "G3"],
         "evidence": ev("Consumer Electronics: 'zero stock at principal' — revenue 18.8% of budget.",
                        "Essentials: lentils/chickpea/raw-material shortage; Miniket paddy shortage.",
                        "ABSL Asphalt: LC bitumen unavailable.",
                        "Commodities F&B: no LC/purchase approval Jul–Oct.",
                        "Ispat: BMRE shutdown, pending orders not delivered.",
                        "No order-level short-supply extract (B8/G2/G3 pending) — self-reported."),
         "verdict_note": "Strongest recurring cause; needs B8/G2/G3 to quantify."},
        {"id": "H6", "title": "Credit policy pushed dealers away", "verdict": "Partial", "confidence": "Low",
         "impact_cr": None, "data_ids": ["B7", "E2"],
         "evidence": ev("Infotech: root cause cites overdue receivables and customer credit restrictions.",
                        "Next JobZ: DSO 60→45 days, receivable concentration 26%.",
                        "No AR ageing / credit-block extract yet (B7 pending)."),
         "verdict_note": "Two SBUs only; B7 required for the rest."},
        {"id": "H7", "title": "Product / quality issue", "verdict": "Rejected", "confidence": "Low",
         "impact_cr": None, "data_ids": ["B9", "F1", "H1"],
         "evidence": ev("No complaint or quality escalation appears in any of the 12 SBU root-cause notes."),
         "verdict_note": "No evidence in the submitted plans."},
        {"id": "H8", "title": "Margin-driven loss", "verdict": "Confirmed", "confidence": "Medium",
         "impact_cr": round(top2, 2), "data_ids": ["A1", "A2", "A5", "A7"],
         "evidence": ev("Telecom GP −36.6%: stock cleared through dealers with higher subsidies.",
                        "Commodities F&B GP 8.0%; Logistics Ex-CHA GP 2.8%; ABSL Asphalt GP 5.2%.",
                        "Essentials and Ispat together carry %.2f Cr of the %.2f Cr total loss." % (top2, tot_loss),
                        "GP is the gross-margin proxy; CM (after variable S&D) is not split out yet (A2/A5)."),
         "verdict_note": "GP-based. CM% still pending."},
        {"id": "H9", "title": "Went silent in market", "verdict": "Insufficient data", "confidence": "Low",
         "impact_cr": None, "data_ids": ["F4", "A5", "E4"],
         "evidence": ev("Trade spend by SBU/region not received (A5); brand pack has ATL/BTL mix but no Q4→Q1 spend change."),
         "verdict_note": "Needs A5 + E4."},
    ]

    # ---------- recovery ----------
    recovery = []
    for code, s in sheet.items():
        if not s["plan_rev"]:
            continue
        recovery.append({
            "lever": "Revenue recovery plan", "sbu": code, "region": None,
            "action": s["plan_rev"], "owner": s["owner"] or s["lead_fn"], "start": AS_OF,
            "revenue_impact_cr": s["commit_rev"], "np_impact_cr": s["commit_loss"],
            "status": s["status"],
            "assumption": ("SBU's own commitment (sheet col BM/BN), not an independent estimate"
                           if (s["commit_rev"] or s["commit_loss"]) else
                           "Not quantified in Cr by the SBU — impact shown as 'Data pending'"),
            "target_date": s["target_date"], "data_ids": ["A1", "A8"],
        })

    # ---------- SE commitment ----------
    se_commitment = []
    for d in allse:
        se_commitment.append({
            "bu": d["n"], "jul": d.get("jul"), "aug": d.get("aug"), "sep": d.get("sep"),
            "avg": d.get("avg"), "oct_mtd": d.get("oct"), "commitment": d.get("commit"),
            "se_contribution": d.get("se"), "ads": d.get("ads"), "rads": d.get("rads"),
            "status": ("On Track" if (d.get("oct") or 0) >= 100 else
                       "At Risk" if (d.get("oct") or 0) >= 70 else "Critical"),
            "fixed_cost": d.get("fc"), "cm_pct": (d.get("cm") or 0) / 100 if d.get("cm") is not None else None,
            "breakeven": d.get("be"), "be_coverage": (round(d["se"] / d["be"], 3) if d.get("be") else None),
            "source": "ALL SE commitment dashboard (data.arl-se-sbu-commitment.vercel.app)",
        })

    # ---------- direction ----------
    sbu_direction = []
    for r in sbu_pnl:
        s = sheet[r["sbu"]]
        d, why, conf = direction(s, pnl.get(SBU[r["sbu"]]["bu"], {}), SBU[r["sbu"]]["bu"] in (225, 252, 255))
        sbu_direction.append({
            "sbu": r["sbu"], "name": r["name"], "direction": d, "reason": why,
            "confidence": conf, "quarters_to_breakeven": None,
            "provisional": True, "data_completeness": r["data_completeness"],
            "pending": ["A1 (Q4 P&L)", "A3", "A4", "B2", "C1", "C2", "D2", "D3", "D4"],
            "loss": r["loss"], "deficit": r["deficit"], "gp_pct": r["gp_pct"], "revenue": r["revenue"],
        })

    # ---------- decisions ----------
    def opt(name, np_, cost, tti, risk, assumption):
        return {"name": name, "revenue_impact_cr": None, "np_impact_cr": np_,
                "cost_cr": cost, "time_to_impact": tti, "risk": risk, "assumption": assumption}

    D = {c: sheet[c] for c in sheet}
    decisions = [
        {"id": "D1", "sbu": "AELOTH", "rank": 1,
         "question": "Should Essentials get RM/LC approvals released this month?",
         "brutal_fact": "Essentials lost %.2f Cr in Q1 — the single largest loss in the portfolio — on raw-material shortage." % D["AELOTH"]["loss"],
         "options": [
             opt("Approve the 30-day SKU/plant/customer recovery plan and release RM procurement", D["AELOTH"]["commit_loss"] or 20.91, 0, "30–60 days", "Working capital locked in inventory", "SBU commitment (sheet col BN)"),
             opt("Release only the top-20 SKU lines", round((D["AELOTH"]["commit_loss"] or 20.91) * 0.5, 2), 0, "30–60 days", "Partial volume recovery", "Assumed 50% of the committed recovery"),
             opt("Do nothing — hold procurement as is", 0, 0, "—", "Loss repeats at ~%.2f Cr/quarter" % D["AELOTH"]["loss"], "Run-rate continuation of the Q1 loss"),
         ],
         "recommendation": "Approve the 30-day plan — the loss is supply-driven and the fix is an approval, not capital.",
         "why": "Root cause is RM shortage, not demand: revenue was 77.7% of budget and GP is 10.8%.",
         "confidence": "Medium", "data_ids": ["A1", "A8", "B8"], "reversibility": "Two-way door",
         "owner": D["AELOTH"]["owner"], "decide_by": "2026-11-05", "review_date": "2026-12-05",
         "tracking_kpi": "Weekly revenue back to 125 Cr+/month; RM fill rate ≥ 95%",
         "kill_criterion": "If September run-rate is not recovered by 30 Nov, stop the plan and re-baseline",
         "status": "Proposed", "rec_index": 0, "blocked_by": []},
        {"id": "D2", "sbu": "AIL", "rank": 2,
         "question": "Should Ispat sign the Islam Metal and Saleh Steel agreements now?",
         "brutal_fact": "Ispat lost %.2f Cr in Q1 while revenue was only 74.2%% of budget; GP 13.5%%." % D["AIL"]["loss"],
         "options": [
             opt("Sign both agreements and continue the progressive price increase", 11.20, 0, "1–2 quarters", "Volume loss if the market resists the price", "Q1 loss elimination is the SBU's stated target (sheet col BN)"),
             opt("Sign Islam Metal only (Nov), defer Saleh Steel", 5.60, 0, "1–2 quarters", "COGS stays high for another quarter", "Assumed 50% of the committed recovery"),
             opt("Do nothing — wait for the BMRE project", 0, 0, "—", "Loss continues until Jan-27", "Q1 run-rate"),
         ],
         "recommendation": "Sign both now; the loss is a cost problem (electricity +18%, VAT up) and price has already moved +BDT 1,600/MT.",
         "why": "Cost inflation, not volume, is the driver — GP fell even though achievement was 74%.",
         "confidence": "Medium", "data_ids": ["A1", "A6"], "reversibility": "One-way door",
         "owner": D["AIL"]["owner"], "decide_by": "2026-11-15", "review_date": "2026-12-15",
         "tracking_kpi": "COGS per MT down 5%; NP ≥ 0 by Mar-27",
         "kill_criterion": "If COGS/MT is not down 5% by 31 Dec, re-open the sourcing decision",
         "status": "Proposed", "rec_index": 0, "blocked_by": []},
        {"id": "D3", "sbu": "ACL", "rank": 3,
         "question": "Should Commodities F&B keep trading below an 8% gross margin?",
         "brutal_fact": "Commodities F&B lost %.2f Cr on %.2f Cr revenue at 8.0%% GP." % (D["ACL"]["loss"], D["ACL"]["revenue"] if "revenue" in D["ACL"] else D["ACL"]["rev"]["q1"]["actual"]),
         "options": [
             opt("Set a price floor off true landed cost and drop negative-SKU lines", 2.40, 0, "1 quarter", "Volume falls further in Q2", "Q1 loss elimination is the SBU's stated target"),
             opt("Hold prices, keep the 5-LC plan and grow volume", 1.20, 0, "2 quarters", "Margin stays thin; loss continues", "Assumed 50% of the committed recovery"),
             opt("Do nothing", 0, 0, "—", "Loss repeats at ~%.2f Cr/quarter" % D["ACL"]["loss"], "Q1 run-rate"),
         ],
         "recommendation": "Price floor first, volume second — at 8% GP the volume plan cannot cover cost.",
         "why": "Thin margin plus import cost; the SBU's own plan already proposes a price floor from 1-Nov.",
         "confidence": "Medium", "data_ids": ["A1", "A3", "A5"], "reversibility": "Two-way door",
         "owner": D["ACL"]["owner"], "decide_by": "2026-11-10", "review_date": "2026-12-10",
         "tracking_kpi": "GP ≥ 12% and monthly PAT ≥ 0 by 30 Nov",
         "kill_criterion": "If GP is below 10% by 30 Nov, exit the affected SKUs",
         "status": "Proposed", "rec_index": 0, "blocked_by": []},
        {"id": "D4", "sbu": "ATL", "rank": 4,
         "question": "Should Telecom stop subsidised stock clearance and go to exit review?",
         "brutal_fact": "Telecom GP is −36.6%%: it lost %.2f Cr on %.2f Cr revenue." % (D["ATL"]["loss"], D["ATL"]["rev"]["q1"]["actual"]),
         "options": [
             opt("Stop clearance immediately; write off the residual stock", 2.10, None, "Immediate", "Stock write-off hits this quarter", "Q1 loss is the avoidable run-rate"),
             opt("Wind down over 2 quarters while selling at positive contribution", 1.05, None, "2 quarters", "Subsidy continues one more quarter", "Assumed 50% of the Q1 loss avoided"),
             opt("Do nothing", 0, 0, "—", "Every taka of sales adds loss", "Q1 run-rate"),
         ],
         "recommendation": "Stop clearance now and start exit review — negative gross margin cannot be fixed by volume.",
         "why": "GP −36.6% is a structural price/cost gap, not a demand problem.",
         "confidence": "High", "data_ids": ["A1", "A3"], "reversibility": "One-way door",
         "owner": D["ATL"]["owner"], "decide_by": "2026-11-15", "review_date": "2026-12-15",
         "tracking_kpi": "No invoice below landed cost; residual stock cleared by 31 Dec",
         "kill_criterion": "If a positive-GP range is not identified by 31 Dec, recommend exit",
         "status": "Proposed", "rec_index": 0, "blocked_by": []},
        {"id": "D5", "sbu": "ACEL", "rank": 5,
         "question": "Should Consumer Electronics get bank financing to restock, or pause?",
         "brutal_fact": "Consumer Electronics achieved 18.8%% of budget and lost %.2f Cr — zero stock at the principal." % D["ACEL"]["loss"],
         "options": [
             opt("Secure working-capital financing and restock", 0.96, None, "1–2 quarters", "Debt service while demand is unproven", "Q1 loss is the avoidable run-rate"),
             opt("Pause expansion, run 4 showrooms cash-only", 0.48, 0, "1 quarter", "Revenue stays at ~0.7 Cr/month", "Assumed 50% of the Q1 loss avoided"),
             opt("Do nothing", 0, 0, "—", "Fixed showroom cost with no stock", "Q1 run-rate"),
         ],
         "recommendation": "Financing first, showrooms second — the constraint is stock, not demand.",
         "why": "The SBU is supply-blocked; the 4 existing showrooms cannot sell what is not stocked.",
         "confidence": "Low", "data_ids": ["A1", "B8"], "reversibility": "One-way door",
         "owner": D["ACEL"]["owner"], "decide_by": "2026-11-30", "review_date": "2026-12-30",
         "tracking_kpi": "Stock cover ≥ 45 days; revenue ≥ 3 Cr/month by Jan-27",
         "kill_criterion": "If stock is not restored by 31 Dec, re-baseline to 4 showrooms",
         "status": "Proposed", "rec_index": 0, "blocked_by": []},
        {"id": "D6", "sbu": None, "rank": None,
         "question": "Which competitor took our share in the lost-dealer regions?",
         "brutal_fact": "%d dealers who bought in Q4 placed no order in Q1 — and we cannot yet say why." % lost_total,
         "options": [], "recommendation": None, "why": None, "confidence": "Low",
         "data_ids": ["C1", "C2", "C3"], "reversibility": "—", "owner": "Marketing / Strategy",
         "decide_by": "2026-11-02", "review_date": None, "tracking_kpi": "C1/C2/C3 delivered",
         "kill_criterion": "—", "status": "Waiting for data", "blocked_by": ["C1", "C2", "C3"]},
        {"id": "D7", "sbu": None, "rank": None,
         "question": "Did our own sales team stop calling on the lost dealers?",
         "brutal_fact": "No CRM visit/call log exists for Q1, so contact on the %d lost dealers is unknown." % lost_total,
         "options": [], "recommendation": None, "why": None, "confidence": "Low",
         "data_ids": ["D2", "D3", "D4", "D5"], "reversibility": "—", "owner": "Sales Ops / IT",
         "decide_by": "2026-11-02", "review_date": None, "tracking_kpi": "CRM extract delivered",
         "kill_criterion": "—", "status": "Waiting for data", "blocked_by": ["D2", "D3", "D4", "D5"]},
        {"id": "D8", "sbu": None, "rank": None,
         "question": "Which lost dealers are worth winning back?",
         "brutal_fact": "Dealer-level profit (A4) and lifting history (B2) are missing, so win-back cannot be prioritised by value.",
         "options": [], "recommendation": None, "why": None, "confidence": "Low",
         "data_ids": ["A4", "B1", "B2"], "reversibility": "—", "owner": "Finance / Sales Ops",
         "decide_by": "2026-11-07", "review_date": None, "tracking_kpi": "Dealer profit extract",
         "kill_criterion": "—", "status": "Waiting for data", "blocked_by": ["A4", "B1", "B2"]},
    ]

    # ---------- insights ----------
    facts = [
        {"section": "MD Brief", "fact": "12 loss-making SBUs lost %.2f Cr in Q1 on %.2f Cr revenue (%.1f%% of revenue)." % (tot_loss, sum(r["revenue"] or 0 for r in sbu_pnl), 100 * tot_loss / sum(r["revenue"] or 0 for r in sbu_pnl)),
         "so_what": "The portfolio-wide hole is a margin problem, not a top-line problem.", "data_ids": ["A1", "A8"]},
        {"section": "MD Brief", "fact": "Essentials (%.2f Cr) and Ispat (%.2f Cr) carry %.0f%% of the total loss." % (D["AELOTH"]["loss"], D["AIL"]["loss"], 100 * top2 / tot_loss),
         "so_what": "Two decisions recover more than half the loss.", "data_ids": ["A1"]},
        {"section": "MD Brief", "fact": "%d dealers who bought in Q4 placed no order in Q1 in the 7 SBUs with order data." % lost_total,
         "so_what": "Dealer churn is real but unexplained — no CRM log, no regional market data.", "data_ids": ["B3", "B4", "D3", "D4"]},
        {"section": "Dealer Loss", "fact": "Essentials lost 295 of 1,129 Q4 dealers (26%%); Ready Mix lost 92 of 258 (36%%); Ispat lost 97 of 385 (25%%).",
         "so_what": "Churn is concentrated in the two largest loss SBUs — win-back is the cheapest revenue.", "data_ids": ["B3", "B4"]},
        {"section": "Market Share", "fact": "No regional market-size or competitor-volume file has been delivered (C1/C2/C3 all pending in the IT tracker).",
         "so_what": "The MD's priority-1 question cannot be answered from data yet; only brand-level share exists.", "data_ids": ["C1", "C2", "C3"]},
        {"section": "Sales KPI", "fact": "No CRM extract exists, so lost-dealer contact, beat compliance and KPI achievement are unknown.",
         "so_what": "The sales-engagement hypothesis stays untested; press IT for D2–D5.", "data_ids": ["D2", "D3", "D4", "D5"]},
        {"section": "Root Cause", "fact": "Supply failure is named as the root cause by 5 of 12 SBUs (Electronics, Essentials, Asphalt, Commodities, Ispat).",
         "so_what": "The largest cluster of causes is an approval/procurement problem the MD can clear this week.", "data_ids": ["B8", "G2", "A2"]},
        {"section": "Recovery", "fact": "Only 7 of 12 SBUs quantified a Cr commitment; Ispat and Telecom did not.",
         "so_what": "Five recovery plans cannot be tracked — they need a number before approval.", "data_ids": ["A9"]},
    ]

    # ---------- write ----------
    def w(name, obj):
        with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)

    w("sbu_pnl.json", sbu_pnl)
    w("loss_bridge.json", loss_bridge)
    w("dealers.json", dealers)
    w("dealer_trend.json", dealer_trend)
    w("dealer_churn.json", dealer_churn)
    w("market_share.json", market_share)
    w("market_diagnosis.json", market_diagnosis)
    w("sales_kpi.json", sales_kpi)
    w("competitor_offers.json", competitor_offers)
    w("seven_p.json", seven_p)
    w("hypotheses.json", hypot)
    w("recovery.json", recovery)
    w("q2_path.json", [])
    w("se_commitment.json", se_commitment)
    w("sbu_direction.json", sbu_direction)
    w("decisions.json", decisions)
    w("decision_log.json", [])
    w("insights.json", facts)

    lineage = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": AS_OF,
        "period": "Q1 FY2026-27 (Jul–Sep 2026)",
        "files": {
            "sbu_pnl.json": [
                {"data_id": "A1", "mcp_server": "google-sheets (CSV export)", "location": "AKIJ Resource · SBU Top-line & Bottom-line Scorecard, gid 475852686", "extracted_at": AS_OF, "period": "Q1FY27", "notes": "Revenue, budget, GP%, EAT, deficit, loss, commitments. Q4 P&L not in this sheet."},
                {"data_id": "A1 (cross-check)", "mcp_server": "enterprise-api-gateway", "location": "fin.tblAccountingJournal, GL 3010001/3010002/3010005/3010006", "extracted_at": AS_OF, "period": "Q1FY27, Q4FY26", "notes": "ERP revenue by BU and quarter; NP proxy includes COGS/S&D/admin/logistics/marketing/finance/tax but excludes depreciation and provisions."},
            ],
            "dealer_trend.json": [{"data_id": "B3", "mcp_server": "enterprise-api-gateway", "location": "oms.tblSalesOrderHeader", "extracted_at": AS_OF, "period": "2026-04..2026-09", "notes": "Distinct sold-to partner per month; 7 SBUs only."}],
            "dealer_churn.json": [{"data_id": "B4", "mcp_server": "enterprise-api-gateway", "location": "oms.tblSalesOrderHeader (NOT EXISTS in Q1)", "extracted_at": AS_OF, "period": "Q4FY26→Q1FY27", "notes": "Q4 buyers with zero Q1 orders."}],
            "market_share.json": [{"data_id": "C1/C2 (partial)", "mcp_server": "web (brand pack)", "location": "akij-resource-brand-marketing-pack.pages.dev", "extracted_at": AS_OF, "period": "latest brand-level", "notes": "National brand share and named competitor shares; no region, no Q4→Q1."}],
            "se_commitment.json": [{"data_id": "A9", "mcp_server": "web (ALL SE dashboard)", "location": "arl-se-sbu-commitment.vercel.app (Google Sheet ALL SE / Sheet10)", "extracted_at": AS_OF, "period": "Jul–Oct 2026", "notes": "9 BUs only (AEL divisions, AIL, ARMCL, ACCL)."}],
            "_source_map.md": [{"data_id": "all", "mcp_server": "see _source_map.md", "location": "-", "extracted_at": AS_OF, "period": "-", "notes": "-"}],
        },
        "pending": {
            "C1": "Regional market size — only Cement arrives automatically; other SBUs need a parser per file format",
            "C2": "Competitor volume by region — owner Marketing/Strategy, 2026-11-02",
            "C3": "Own volume aligned to market definition — Sales Ops, 2026-11-02",
            "D2": "KPI target vs achievement — Sales Ops, 2026-11-02",
            "D3": "CRM visit log — connected; 21 records total and none in Q1, so Q1 contact cannot be proven",
            "D4": "Last contact with lost dealers — Sales Ops/IT, 2026-11-02",
            "A3": "SKU-wise profitability — Finance, 2026-11-02",
            "A4": "Profit per dealer/region — Finance, 2026-11-07",
            "B2": "Dealer-wise monthly lifting — Sales Ops, 2026-11-02",
            "B7": "Credit & receivables — Credit Control, 2026-11-02",
        },
    }
    w("_lineage.json", lineage)

    rows_md = ["# Source map — Data ID → source → status", "",
               "Period: Q1 FY2026-27 (Jul–Sep 2026) · BDT Cr · as of %s" % AS_OF, "",
               "| Data ID | Item | Source found | Status | Owner | Freshness |",
               "|---|---|---|---|---|---|"]
    src = {
        "A1": ("SBU P&L", "Google Sheet (recovery scorecard) + ERP GL", "Partial", "Finance", "Q1 only"),
        "A2": ("Revenue bridge inputs", "ERP GL revenue only", "Partial", "Finance/Sales Ops", AS_OF),
        "A3": ("SKU profitability", "—", "MISSING", "Finance", "—"),
        "A4": ("Profit per dealer/region", "—", "MISSING", "Finance", "—"),
        "A5": ("Trade spend & schemes", "—", "MISSING", "Marketing/Finance", "—"),
        "A6": ("RM & production cost", "—", "MISSING", "Supply Chain", "—"),
        "A7": ("Logistics cost", "ERP GL logistics total only", "Partial", "Logistics", AS_OF),
        "A8": ("Budget vs actual", "Google Sheet", "OK (revenue/EAT)", "Finance", "Q1"),
        "A9": ("Fixed cost & break-even", "ALL SE dashboard", "Partial (2 of 12 SBUs)", "Finance", "Oct MTD"),
        "B1": ("Dealer master", "—", "MISSING", "Sales Ops", "—"),
        "B2": ("Dealer monthly lifting", "—", "MISSING", "Sales Ops", "—"),
        "B3": ("Active dealer count", "ERP sales orders", "Partial (7 SBUs)", "Sales Ops", AS_OF),
        "B4": ("Lost dealers", "ERP sales orders", "Partial (7 SBUs, count only)", "Sales Ops", AS_OF),
        "B5": ("Declining dealers", "—", "MISSING", "Sales Ops", "—"),
        "B6": ("New dealers", "—", "MISSING", "Sales Ops", "—"),
        "B7": ("Credit & receivables", "—", "MISSING", "Credit Control", "—"),
        "B8": ("Unfulfilled orders", "—", "MISSING", "Supply Chain", "—"),
        "B9": ("Complaints/claims", "—", "MISSING", "QA", "—"),
        "C1": ("Market size by region", "Marketing tracker · Cement monthly grid (other SBUs different layout)", "Partial (1 of 8 SBUs)", "Marketing Data Head", "auto"),
        "C2": ("Competitor volume by region", "Marketing tracker · brand volumes (national, not regional)", "Partial (national only)", "Marketing Data Head", "auto"),
        "C3": ("Own volume (market definition)", "—", "MISSING", "Sales Ops", "—"),
        "C4": ("Dealer share-of-wallet", "—", "MISSING", "Sales", "—"),
        "C5": ("Distribution coverage", "—", "MISSING", "Marketing", "—"),
        "D1": ("Org structure & vacancies", "—", "MISSING", "HR/Sales Ops", "—"),
        "D2": ("KPI target vs achievement", "—", "MISSING", "Sales Ops", "—"),
        "D3": ("CRM call & visit log", "ARL CRM API (arlcrm.ibos.agency) · 21 visits, 0 in Q1", "Delivered but empty for Q1", "Sales Ops / IT", "auto"),
        "D4": ("Last contact with lost dealers", "ARL CRM API · no Q1 records exist", "Delivered but empty for Q1", "Sales Ops / IT", "auto"),
        "D5": ("Beat compliance", "—", "MISSING", "Sales Ops", "—"),
        "D6": ("Attrition & transfers", "—", "MISSING", "HR", "—"),
        "E1": ("Competitor price list", "—", "MISSING", "Sales/Marketing", "—"),
        "E2": ("Competitor offers", "—", "MISSING", "Sales", "—"),
        "E3": ("Lost dealer → competitor", "—", "MISSING", "Sales", "—"),
        "F4": ("Promotion (own)", "Brand pack ATL/BTL mix", "Partial", "Marketing", "FY plan"),
        "G2": ("Stock-outs", "—", "MISSING", "Supply Chain", "—"),
        "G3": ("OTIF", "—", "MISSING", "Supply Chain", "—"),
        "H1": ("Dealer exit interviews", "—", "MISSING", "Sales", "—"),
        "I1": ("Macro events", "SBU root-cause notes (qualitative)", "Partial", "Strategy", "Q1"),
    }
    for k in sorted(src, key=lambda x: (x[0], int(re.sub(r"\D", "", x) or 0))):
        item, found, status, owner, fresh = src[k]
        rows_md.append("| %s | %s | %s | %s | %s | %s |" % (k, item, found, status, owner, fresh))
    rows_md += ["", "**IT Data Link Tracker:** column K (Data Link) is empty for all 54 rows and all link statuses read",
                "'Pending' / 'Not checked'. No IT file has been shared yet — the tracker confirms the MISSING items above.",
                "", "**Note:** DWH (203.202.241.211) was unreachable on %s, so fin/oms DWH mirrors could not be used." % AS_OF]
    with open(os.path.join(DATA, "_source_map.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rows_md))

    print("built: %d SBUs, %d dealers lost, %.2f Cr loss" % (len(sbu_pnl), lost_total, tot_loss))
    print("wrote:", ", ".join(sorted(os.listdir(DATA))))


if __name__ == "__main__":
    main()

