#!/usr/bin/env python3
"""Validate dashboard JSON snapshots against references/data-contract.md.

Usage: python scripts/validate_data.py data/
Exit code 1 if any ERROR. Warnings do not fail the build but must be reviewed.
No third-party dependencies.
"""
import json, os, sys

REQUIRED = {
    "sbu_pnl.json": ["sbu", "period", "revenue", "net_profit"],
    "loss_bridge.json": ["sbu", "q4_np", "volume", "price", "mix", "cost", "fixed", "q1_np"],
    "dealers.json": ["dealer_code", "sbu", "region", "q4fy26", "q1fy27", "status"],
    "dealer_trend.json": ["sbu", "region", "month", "active_dealers"],
    "market_share.json": ["sbu", "region", "period", "market_volume", "own_volume", "competitors", "source"],
    "market_diagnosis.json": ["sbu", "region", "pp_change", "market_change", "diagnosis"],
    "sales_kpi.json": ["sbu", "region", "employee_id", "vol_target", "vol_actual"],
    "seven_p.json": ["p", "attribute", "own_q1"],
    "hypotheses.json": ["id", "title", "verdict", "evidence", "data_ids"],
    "recovery.json": ["lever", "sbu", "action", "owner", "np_impact_cr"],
    "se_commitment.json": ["bu", "commitment", "breakeven"],
    "insights.json": ["section", "fact", "so_what", "data_ids"],
    "sbu_direction.json": ["sbu", "direction", "reason", "confidence"],
    "decisions.json": ["id", "question", "options", "recommendation", "owner", "decide_by", "data_ids"],
}
PERIODS = {"Q1FY27", "Q4FY26", "Q1FY26"}
VERDICTS = {"Confirmed", "Partial", "Rejected", "Insufficient data"}
DIAG = {"Market shrank", "Share lost to competitor", "Both", "Stable", "Insufficient data"}
errors, warnings = [], []

def load(d, f):
    p = os.path.join(d, f)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as e:
        errors.append(f"{f}: invalid JSON ({e})"); return None

def main(d):
    data = {}
    for f, req in REQUIRED.items():
        rows = load(d, f)
        if rows is None:
            warnings.append(f"{f}: missing — section must show 'Data pending'"); continue
        if not isinstance(rows, list):
            errors.append(f"{f}: must be a JSON array"); continue
        data[f] = rows
        for i, r in enumerate(rows):
            for k in req:
                if k not in r:
                    errors.append(f"{f}[{i}]: missing key '{k}'")
            if "period" in r and r["period"] not in PERIODS:
                errors.append(f"{f}[{i}]: bad period {r['period']!r}")
            for k, v in r.items():
                if (k.endswith("_pct") or k.endswith("_share") or k.startswith("own_share")) and isinstance(v, (int, float)) and abs(v) > 1.5:
                    warnings.append(f"{f}[{i}].{k}={v}: looks like a whole-number %, store fractions")

    # loss bridge reconciliation
    for i, r in enumerate(data.get("loss_bridge.json", [])):
        try:
            parts = sum(r.get(k) or 0 for k in ("volume", "price", "mix", "cost", "fixed", "unexplained"))
            calc = r["q4_np"] + parts
            if abs(calc - r["q1_np"]) > max(0.01, abs(r["q1_np"]) * 0.01):
                errors.append(f"loss_bridge[{i}] {r['sbu']}: bridge {calc:.2f} != q1_np {r['q1_np']:.2f}")
        except (KeyError, TypeError):
            pass

    # bridge vs P&L
    pnl = {(r.get("sbu"), r.get("period")): r for r in data.get("sbu_pnl.json", [])}
    for r in data.get("loss_bridge.json", []):
        p = pnl.get((r.get("sbu"), "Q1FY27"))
        if p and p.get("net_profit") is not None and abs(p["net_profit"] - r.get("q1_np", 0)) > 0.01:
            errors.append(f"{r['sbu']}: loss_bridge q1_np != sbu_pnl Q1 net_profit")

    # market share sanity
    for i, r in enumerate(data.get("market_share.json", [])):
        mv, ov = r.get("market_volume"), r.get("own_volume")
        comp = sum((c.get("volume") or 0) for c in r.get("competitors", []))
        if mv and ov is not None and ov + comp > mv * 1.02:
            errors.append(f"market_share[{i}] {r.get('region')} {r.get('period')}: own+competitors exceed market")
        if not r.get("source"):
            errors.append(f"market_share[{i}]: source required")
    for i, r in enumerate(data.get("market_diagnosis.json", [])):
        if r.get("diagnosis") not in DIAG:
            errors.append(f"market_diagnosis[{i}]: bad diagnosis {r.get('diagnosis')!r}")

    for i, r in enumerate(data.get("hypotheses.json", [])):
        if r.get("verdict") not in VERDICTS:
            errors.append(f"hypotheses[{i}]: bad verdict {r.get('verdict')!r}")
        if r.get("verdict") in ("Confirmed", "Partial") and not r.get("evidence"):
            errors.append(f"hypotheses[{i}] {r.get('id')}: verdict needs evidence")

    # orphan keys: dealers -> sales_kpi employees
    emps = {r.get("employee_id") for r in data.get("sales_kpi.json", [])}
    if emps:
        orphans = {r.get("employee_id") for r in data.get("dealers.json", []) if r.get("employee_id") and r.get("employee_id") not in emps}
        if orphans:
            warnings.append(f"dealers.json: {len(orphans)} employee_id(s) not in sales_kpi.json (e.g. {sorted(orphans)[:3]})")

    for r in data.get("recovery.json", []):
        if r.get("np_impact_cr") is not None and not r.get("assumption"):
            warnings.append(f"recovery '{r.get('lever')}': impact without stated assumption")

    DIRS = {"Fix & Recover", "Refocus", "Hold & Protect", "Restructure / Exit review", "Insufficient data"}
    for i, r in enumerate(data.get("sbu_direction.json", [])):
        if r.get("direction") not in DIRS:
            errors.append(f"sbu_direction[{i}]: direction must be one of {sorted(DIRS)}")
    pnl_sbus = {r.get("sbu") for r in data.get("sbu_pnl.json", []) if r.get("period") == "Q1FY27" and (r.get("net_profit") or 0) < 0}
    dir_sbus = {r.get("sbu") for r in data.get("sbu_direction.json", [])}
    for s_ in sorted(pnl_sbus - dir_sbus):
        errors.append(f"loss-making SBU '{s_}' has no direction in sbu_direction.json")
    for i, r in enumerate(data.get("decisions.json", [])):
        opts = r.get("options") or []
        if r.get("status") != "Waiting for data":
            if len(opts) < 2:
                errors.append(f"decisions[{i}] {r.get('id')}: needs at least 2 options (incl. do-nothing)")
            if not any("nothing" in (o.get("name") or "").lower() for o in opts):
                warnings.append(f"decisions[{i}] {r.get('id')}: no 'do nothing' baseline option")
            if any(o.get("np_impact_cr") is None for o in opts):
                errors.append(f"decisions[{i}] {r.get('id')}: every option needs np_impact_cr")
        elif not r.get("blocked_by"):
            errors.append(f"decisions[{i}] {r.get('id')}: 'Waiting for data' needs blocked_by Data IDs")
    top = [r for r in data.get("decisions.json", []) if isinstance(r.get("rank"), int) and r["rank"] <= 5]
    if len(top) > 5:
        errors.append("more than 5 decisions ranked in the top 5")

    if not os.path.exists(os.path.join(d, "_lineage.json")):
        errors.append("_lineage.json missing — every number needs a source")

    for w in warnings: print("WARN ", w)
    for e in errors: print("ERROR", e)
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "data"))
