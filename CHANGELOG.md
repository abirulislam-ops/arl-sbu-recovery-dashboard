# Changelog — MD decision cockpit rebuild

Period: Q1 FY2026-27 (Jul–Sep 2026). All money in BDT Cr.
Rollback: the previous single-file build is kept as `index.prev.html`.

## Phase 1 — Audit (`data/audit_report.md`)

28 findings, 5 critical. Nothing was changed in this phase; everything below is the fix.

| SBU | Found | Resolution |
|---|---|---|
| AELOTH | GP% stored 10.8% vs recomputed −34.4% (COGS 496.75 > revenue 369.57) | flagged in cockpit; GP% still shown from the scorecard with a warning note |
| ARMCL | GP% 12.7% vs 20.6% recomputed | flagged |
| ACL | GP% 8.0% vs −22.4% recomputed | flagged |
| ABSLASP | GP% 5.2% vs −20.2%; Lube Oil tab used as its share | share **removed**, marked "no asphalt share data" |
| ALL | EBITDA 28.78 on revenue 8.55 (impossible) | EBITDA no longer displayed |
| AIL | commit 62.7 Cr derived (7,052 MT x 89,000) | shown as *stated* commitment, not firm |
| Portfolio | coverage 83% inflated by derived commits | KPI renamed **"Stated commitment"** with the caveat |
| All | header badges rendered "—" until JS ran | now static in the HTML |
| All | same loss figure repeated up to 13 times | one home per metric (Loss Map), SBU pages link to it |

## Phase 2 — Data

- `data/market_share_tidy.json` — 2,079 rows from 9 tabs of the workbook (two-row header flattened, share≈sales/total ±0.5 pp check, `#DIV/0!`/−100%/blank treated as missing, partial months flagged).
- `data/market_share_summary.json` — Q4 FY26 vs Q1 FY27 averages, only where the series is trustworthy:
  - **AIL**: 3.05% → 2.92% (−0.13 pp); top gainer **AKS +2.51 pp**
  - **ALL**: 1.00% → 0.67% (−0.33 pp)
- Gaps kept as gaps: `MS-ARMCL` (header incomplete), `MS-ALCL/ACEL/AMPL/ACL/AELOTH` (period/total mismatch), `MS-ABSLASP` (wrong market), `MS-ATL/NJL/AITL` (no tab).

## Phase 3 — Analysis

`src/analysis/analysis.js` (pure functions) + `tests/test_analysis.js` — 16 tests pass:
loss bridge, share loss, 7P gap with industry weights, 2x2 game, direction rules, plan credibility, break-even, share-recovery EAT, portfolio allocator.

## Phase 4 — Restructure

- New single file built by `scripts/build_cockpit.js` (103 KB, 21 pages).
- Navigation and SBU order exactly per skill §5; SBU pages follow the fixed 10-section order.
- Removed from the MD surface and moved to Data & Sources: the 64 KB link registry, the 27 KB regional-leader matrix, the duplicated scorecard and the Sales KPI page (its content now lives in Loss Map + Root Cause).

## Assumptions added (all labelled on screen)

1. **Loss bridge**: revenue effect = (budget revenue − actual) × actual GP%. Residual = cost/finance/mix, **not decomposed** (no budget GP%, no unit data).
2. **Game matrix**: price elasticity −1.2 and the rival matching 60% of any price cut; every matrix is stamped **illustrative**.
3. **7P weights**: rebar Price 0.35 / Place 0.25; other SBUs use default weights until scored.
4. **Plan credibility**: Credible = commit ≥ 90% of deficit and break-even inside 6 months; Stretch = ≥ 50%; otherwise Not credible.

## Not done (gaps, shown on screen)

- Region-wise competitor share (C1/C2) for 10 of 12 SBUs.
- 7P scores for 11 of 12 SBUs.
- Break-even date per SBU.
- PeopleDesk vacancy/attrition (D1/D6) and AR ageing (B7).

## Deploy

Not deployed. Awaiting approval; previous build preserved in `index.prev.html`.
