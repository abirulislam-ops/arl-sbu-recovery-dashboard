# AGENTS.md — ARL SBU Loss Recovery Dashboard

> Working rules for OpenCode agents. Full details are in `README.md` — read it first.

## What this is

A self-contained, single-file HTML dashboard (`index.html`) diagnosing the Q1 FY2026-27 losses of
AKIJ Resource's 12 loss-making SBUs and judging whether their recovery plans reach Q2 profit.
**No build step** — the whole app is one `<script>` containing a `SBUS` data array plus render
functions. Deployed on Vercel from `main`.

## Golden rules

1. **Never estimate or reuse stale figures.** Every number comes from a live source — query it:
   - **Recovery plans / commitments / owners** → the Google Sheet (see README §6.1 for id + CSV URL).
   - **Live ERP revenue/orders/customers/AR** → the `enterprise-api-gateway` MCP
     (`execute_readonly_query`, `describe_table`, `search_tables`).
   - **LifeCare pharmacy POS/P&L** → the `lifecare_portal` MCP (`call_api`, `list_offices`).
   - **Market/macro context** → web search (cite in the External cards).
2. **Never commit secrets.** The repo is public. No tokens, passwords, or connection strings.
3. **Full SBU names in visible text**, never the bare code (e.g. "Consumer Electronics", not "ACEL").
4. **Money is BDT crore** throughout.
5. **Verify before pushing:** extract the `<script>` and run `node --check` on it.

## The data model

- `SBUS[]` — SBU objects (revenue/EAT/deficit/loss/commit/scope + 3 internal problem cards +
  `dealers` (Retention) + `external` + plan + Q2 verdict + recommendations). See README §5.
- `META{}` — per-`code` metadata: business head, loss region, avg order value, new customers,
  commitments (with periods), owner, People/Process/Technology.
- `BE{}` — break-even month per SBU (overview timeline).
- At load: surplus (loss 0) SBUs are spliced out and the rest sorted most-loss-first.

## Add / update an SBU

1. Pull the sheet, confirm the SBU's BA–BQ (CSV cols 52–68) are filled.
2. Edit `index.html`: append a `SBUS` object + a `META` entry + a `BE` entry.
3. `commit: null` for "Loss only"/"Revenue achieved" SBUs.
4. Ordering is automatic — do not hand-position entries.

## Deploy

```powershell
git add index.html
git commit -m "Update <SBU> …"
git push origin main
```

Vercel redeploys automatically. If `gh` auth is invalid: `"<PAT>" | gh auth login --with-token`.
