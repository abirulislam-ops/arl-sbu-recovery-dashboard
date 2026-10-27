# ARL SBU Loss Recovery — Diagnostic Dashboard

A self-contained, single-file HTML dashboard that diagnoses why five (now six) AKIJ Resource SBUs are losing money in Q1 FY2026-27, what their recovery plans are, and whether those plans reach Q2 profit.

## What it covers

- **Overview + SBU-wise tabs** — an Overview tab linked to one tab per SBU.
- **Internal problems** — customer acquisition, sales, business degression, and dealer/customer-loss reasons.
- **External problems** — market / regulatory / macro factors (from the recovery-plan root-cause notes + current web context).
- **Revenue recovery — committed vs required** — coverage of each SBU's Q1 revenue deficit.
- **Break-even vs the Q2 window** — when each loss-maker reaches monthly EAT break-even.
- **Q2-profit judgement** — whether the recovery plan recovers Q1 and reaches profit within Q2.

## SBUs covered

Consumer Electronics · Logistics – Ex-CHA · LifeCare – Pharmacy · Essential – Trading · Nobayon · Next JobZ

## Data sources

- **iBOSDDD ERP** (revenue via `fin.tblAccountingJournal`, GL 3010001/2/5/6)
- **AR SBU Top-line & Bottom-line Scorecard** (recovery plans, BA–BQ)
- **Akij Pharmacy portal** (`akijpharma.ibos.io`) — outlet network for LifeCare

## Deploy

This is a static site — the whole dashboard is `index.html`. Deploy it anywhere (Vercel, GitHub Pages, Netlify) with no build step.

---

*All revenue/deficit/loss figures are measured ERP facts; the acquisition–sales–degression diagnosis and recommendations are analyst interpretation.*
