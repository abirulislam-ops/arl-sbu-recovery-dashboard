# ARL SBU Loss Recovery — Diagnostic Dashboard

A **self-contained, single-file HTML dashboard** (no build step, no CDN, no framework) that diagnoses
why AKIJ Resource's loss-making SBUs are losing money in **Q1 FY2026-27 (Jul–Sep 2026)**, what their
recovery plans are, and whether those plans reach Q2 profit.

Live site: **https://arl-sbu-recovery-dashboard.vercel.app** (Vercel auto-deploys from `main`).

---

## 1. What this project is

One HTML file (`index.html`) = the entire application. It renders:

- **Overview** — portfolio KPIs (revenue deficit, net loss, commitments, coverage), a
  "revenue recovery — committed vs required" chart, a "break-even vs the Q2 window" timeline, and a
  full scorecard table (SBU, business head, deficit, loss, commitment, coverage, Q2 verdict).
- **One page per loss-making SBU** (collapsible left sidebar, most-loss-first), each showing:
  - **Internal problems** — 4 cards: Acquisition · Conversion · Retention · Business degression.
  - **External problems** — market / regulatory / macro factors.
  - **Monthly revenue** chart (budget vs actual, Jul/Aug/Sep).
  - **Q2-profit verdict** — whether the plan recovers Q1 and reaches profit within Q2.
  - **Recovery plan** + **Commitment & accountability** (top-line/bottom-line commitment, action
    owner, People/Process/Technology) + **Optimized recommendations**.
  - **Scorecards** — Q1 revenue budget/actual, deficit, EAT, commitment, coverage, **Avg Order
    Value** and **New Customers (Q1)** (ERP-derived where the SBU sells through sales orders).

There is **no server logic** — all rendering is client-side JavaScript. The data is embedded as a
JS array (`SBUS`) inside the single `<script>` tag.

---

## 2. SBUs covered

**12 loss-making SBUs** (surplus SBUs are hidden at load — see §9):

Consumer Electronics · Logistics – Ex-CHA · LifeCare – Pharmacy · Next JobZ · Telecom ·
Essentials · Ready Mix · Commodities – F&B · ABSL – Asphalt · Infotech · Ispat · Mediplex

*(Two profitable SBUs — Essential – Trading and Nobayon — exist in the data but are filtered out
because their loss = 0.)*

---

## 3. Repo layout

```
arl-sbu-recovery-dashboard/
├── index.html            # the entire dashboard (renders MD Brief first)
├── data/                 # validated JSON snapshots — the source of truth for numbers
│   ├── sbu_pnl.json, sbu_direction.json, decisions.json, hypotheses.json …
│   ├── _lineage.json     # every file → Data ID → MCP server → extraction time
│   ├── _source_map.md    # Data ID → source → status → owner
│   └── _raw/             # raw extracts (sheet CSV, ERP, brand pack, ALL SE) — not deployed
├── scripts/
│   ├── build_data.py     # rebuilds data/*.json from data/_raw/*
│   ├── validate_data.py  # schema + reconciliation checks (must be 0 errors)
│   └── embed_data.py     # inlines the JSON into index.html (site has no runtime API)
├── README.md
└── AGENTS.md
```

> **There is no build step.** Edit `index.html` → commit → push → Vercel redeploys.

---

## 4. How the code is organized (inside `index.html`)

The file is HTML + CSS (`<style>`) + one big `<script>`. Inside the script:

| Symbol | What it holds |
|--------|---------------|
| `SBUS`  | The array of SBU objects (the data model — see §5). Surplus SBUs (loss 0) are spliced out, then sorted most-loss-first at load. |
| `META`  | A per-SBU lookup keyed by `code`: `head` (business head), `region` (loss region), `avgOrder` / `newCust` (ERP order scorecards), `revTxt` / `eatTxt` / `timeline` (commitments with periods), `owner`, `people`, `process`, `tech`. |
| `BE`    | Break-even month per SBU (`i` = month slot 0=Jul…11=Jun; >11 = beyond Jun-27), used by the overview timeline. |
| `SEV`, `ICONS`, `TONEC` | Severity levels, SVG icons, tone→colour map. |
| `renderMenu()` / `switchPage()` | Sidebar + page switching (Overview + one pane per SBU). |
| `renderOverview()` | KPIs + profit-gap + scorecard table. |
| `renderSbu()` | Renders each SBU page (problems, chart, verdict, plan, commitments, recommendations). |
| `profitGapHTML()` / `timelineSVG()` / `svgTrend()` | The overview recovery chart, break-even timeline, and monthly revenue chart. |

**Key load-time logic** (near the bottom of the script):

```js
SBUS.splice(0, SBUS.length, ...SBUS.filter(s=>s.loss>0)); // hide surplus (loss 0) SBUs
SBUS.sort((a,b)=>b.loss-a.loss);                          // most loss-making first
```

---

## 5. The SBU data model (`SBUS` entry)

```js
{
  code:'ACEL', name:'Consumer Electronics', group:'Others', rankRev:26, rankEat:22,
  rev:{ jul:{b:1.36,a:0.78}, aug:{b:3.48,a:0.54}, sep:{b:5.30,a:0.59},
        q1:{budget:10.14, actual:1.91, deficit:8.23, ach:'18.8%'} },   // deficit = budget − actual
  eatQ1:-0.96,            // Q1 EAT actual (negative = loss)
  deficit:8.24,           // top-line deficit, column 48 — positive = deficit, 0 = none
  loss:0.96,              // net loss, column 49
  commit:1.0,             // revenue commitment (Cr), column 64 — null if not quantified
  scope:'Revenue + Loss', // column 51
  status:'In progress',   // column 67
  verdict:{label:'Insufficient', tone:'bad'},           // tone: bad | warn | good | info
  problems:{                                            // 3 internal cards
    acquisition:{sev:'critical', headline:'…', metric:{v:'4',l:'showrooms'}, points:['…','…']},
    sales:      {sev:'critical', headline:'…', metric:{v:'18.8%',l:'Q1 ach.'}, points:['…','…']},
    degression: {sev:'critical', headline:'…', metric:{v:'0.59',l:'Sep actual Cr'}, points:['…','…']}
  },
  dealers:{sev:'high', headline:'…', metric:{v:'0',l:'CRM'}, points:['…','…']},  // 4th card = "Retention"
  external:{sev:'high', headline:'…', metric:{v:'0',l:'stock'}, points:['…','…']}, // External card
  planShort:'…',                                          // 1-line recovery plan
  q2:{tone:'warn', label:'…', detail:'…'},                // Q2-profit verdict
  rec:{priority:'high', unlock:'…', actions:['…','…']}    // Optimized recommendations
}
```

Then add a **`META`** entry keyed by `code` (business head, loss region, order scorecards,
commitments, owner, People/Process/Technology), and (if applicable) a **`BE`** entry (break-even
month) so the overview timeline + scorecards stay complete.

Severity levels: `critical` (red) · `high` (orange) · `medium` (amber) · `low` (green) · `none` (grey).

---

## 6. Data sources (where every number comes from)

> **Golden rule: never estimate or reuse stale figures — query the live source every time.**

### 6.1 Google Sheet — the recovery plans (primary input)

The SBU recovery plans live in a view-only Google Sheet ("AKIJ Resource · SBU Top-line &
Bottom-line Scorecard — Revenue Deficit and Loss Recovery Plan").

- **Sheet ID:** `1W-Y6vGGhxNjtOYRB_F72pNGHRV2n9MYPcElwewfLw0U`
- **Tab gid:** `475852686`
- **CSV export:**
  `https://docs.google.com/spreadsheets/d/1W-Y6vGGhxNjtOYRB_F72pNGHRV2n9MYPcElwewfLw0U/export?format=csv&gid=475852686`

Columns **A–AZ** are read-only baseline/budget/rank/trend. Columns **BA–BQ** are the **SBU INPUT**
(recovery plan). **An SBU is "in the dashboard" only when its BA–BQ columns (CSV indices 52–68)
are filled.**

BA–BQ map (CSV index → column → meaning):

| Idx | Col | Meaning | Idx | Col | Meaning |
|-----|-----|---------|-----|-----|---------|
| 52 | BA | Root cause — revenue deficit | 60 | BI | Action owner (name & designation) |
| 53 | BB | Revenue recovery plan | 61 | BJ | People — change required |
| 54 | BC | Revenue recovery actions | 62 | BK | Process — change required |
| 55 | BD | Root cause — net loss | 63 | BL | Technology — change required |
| 56 | BE | Loss recovery plan | 64 | BM | **Revenue commitment (Cr)** |
| 57 | BF | Loss recovery actions | 65 | BN | EAT / loss commitment (Cr) |
| 58 | BG | Lead function | 66 | BO | Target date |
| 59 | BH | Supporting functions | 67 | BP | Status |

Other key columns: `1`=code, `2`=name, `3`=group, `4`=rev rank, `5`=EAT rank, `6–26`=monthly+Q1
revenue, `27–43`=monthly+Q1 EAT, `48`=top-line deficit (Cr), `49`=net loss (Cr), `51`=scope.

**Sign convention:** the sheet's "Deficit/(Surplus)" = `actual − budget` (negative = deficit). The
separate "Top-line deficit" (col 48) and "Net loss" (col 49) are positive-only adverse amounts.
In the JS: `deficit` = col 48, `loss` = col 49, `rev.q1.deficit` = `budget − actual`.

### 6.2 iBOSDDD ERP — live transactions (via the `enterprise-api-gateway` MCP)

Live ERP figures are read through the **`enterprise-api-gateway` MCP** (`execute_readonly_query`,
`describe_table`, `search_tables`, `list_stored_procedures`, `execute_stored_procedure`). This is a
read-only SQL gateway to the iBOSDDD database (schemas `fin`, `oms`, `prt`, etc.).

- **Revenue** (locked definition): GL codes `3010001 + 3010002 + 3010005 + 3010006`, net of returns —
  `SUM(-numAmount) / 10000000.0` (result in crore) from `fin.tblAccountingJournal`.
- **Business-unit id map** (use in `WHERE intBusinessUnitId IN (…)`):

  | SBU | intBusinessUnitId | | SBU | intBusinessUnitId |
  |-----|----|----|-----|----|
  | Essentials (AELOTH) | 144 | | LifeCare (ALCL) | 239 |
  | Ispat (AIL) | 224 | | Infotech (AITL) | 138 |
  | Ready Mix (ARMCL) | 175 | | ABSL – Asphalt (ABSLASP) | 220 |
  | Logistics – Ex-CHA (ALL) | 225 | | Commodities – F&B (ACL) | 221 |
  | Telecom (ATL) | 241 | | Consumer Electronics (ACEL) | 249 |
  | Next JobZ (NJL) | 252 | | Mediplex (AMPL) | 255 |

- **Order metrics** (avg order value, new/lost customers) come from `oms.tblSalesOrderHeader`
  (join to `prt.tblBusinessPartner` for district/region via a derived table — the gateway injects a
  security predicate, so multi-table queries must use a subquery with an explicit `WHERE`).

### 6.3 Akij Pharmacy portal — LifeCare POS data (via the `lifecare_portal` MCP)

LifeCare – Pharmacy retail data comes from the **MANAGERIUM/iBOS portal** at `akijpharma.ibos.io`
(read-only, AES-encrypted API). A `lifecare_portal` MCP connector (`call_api`, `list_offices`,
`list_endpoints`) handles auth + decryption. **Per-user login (mobile + password); the password is
never stored** — only a session token in `~/.lifecare_portal/session.json` (expires ~24 h).

Known endpoints (see `list_endpoints()`): `POSSalesReport/DateWiseDeptOfficeSalesReport`,
`POSSalesReport/NetProfitLossByDepartmentNew`, `ActivityPermission/GetOfficeDDLForGlobal` (33 outlets).

### 6.4 Web — market & macro context (for External cards)

Current market prices, competitor moves, tariffs and macro figures (e.g. rod prices, power tariff,
freight rates, food inflation) are looked up from the web at edit time and cited in the External
problem cards.

---

## 7. How to add / update an SBU

1. **Pull the sheet** (CSV export above) and find the SBU row; confirm its BA–BQ (52–68) are filled.
2. **Edit `index.html`** and append a new `{ … }` object to the `SBUS` array (before the closing
   `];`), plus a matching `META` entry and a `BE` entry.
3. Fill the fields per §5 from the sheet columns (revenue/EAT/deficit/loss/commit/scope/status, the
   3 problem cards + retention + external, plan, verdict, recommendations).
4. **Use the full SBU name** in visible text — never the bare `code`.
5. `commit: null` for "Loss only"/"Revenue achieved" SBUs (no revenue commitment).
6. **Ordering is automatic** — `SBUS.sort((a,b)=>b.loss-a.loss)` places it by Q1 loss; don't
   position it manually.
7. For ERP-derived numbers (order value, new/lost customers, outstanding AR, loss region), query the
   gateway MCP and drop the figures into the cards' `points`/`metric`.

## 8. Deploy (commit + push)

```powershell
Set-Location "C:\Abir\Akij Resources\Strategic planning Department\arl-sbu-recovery-dashboard"
git add index.html
git commit -m "Update <SBU> …"
git push origin main
```

- Branch is `main`; **Vercel auto-deploys on push** (static site, no build command).
- `gh` is authenticated as the repo owner (`abirulislam-ops`); if the token is invalid:
  `"<PAT>" | gh auth login --with-token` (or set `$env:GH_TOKEN`).
- Collaborators push with their own GitHub identity.

## 9. Verify before pushing

```powershell
# extract the <script> and syntax-check it (a missing comma in SBUS is the most common break)
python -c "import re;open('check.js','w',encoding='utf-8').write(re.search(r'<script>(.*)</script>', open('index.html',encoding='utf-8').read(), re.S).group(1))"
node --check check.js
```

Then open `index.html` in a browser and confirm the sidebar item + page render and sit at the right
loss rank.

## 10. Conventions & gotchas

- **Full names, not codes** in all visible labels.
- **Money in BDT crore** throughout.
- **`deficit` (top-level) = col 48** (0 for surplus/"Loss only"); **`rev.q1.deficit` = budget − actual**.
- **Surplus SBUs (loss 0) are hidden** via the `SBUS.splice(…filter(s=>s.loss>0))` line — remove it to
  unhide Essential – Trading and Nobayon.
- **Loss-only SBUs** (e.g. Telecom, Commodities–F&B) have `deficit:0, commit:null` — they appear in the
  sidebar + SBU page but not in the revenue-recovery / break-even charts.
- **Sidebar is collapsible** (top-right `«`/`»` button).
- **Sheet must be "Anyone with link → Viewer"** or the CSV export returns 401.
- **Fact vs interpretation:** revenue/deficit/loss are ERP-verified facts; the
  Acquisition/Conversion/Retention/degression diagnosis, Q2 verdict and recommendations are analyst
  interpretation (flagged in the dashboard footer).

## 11. Security notes

- The repo is **public** — never commit passwords, tokens, or connection strings.
- ERP access goes through the `enterprise-api-gateway` MCP (already configured on your machine).
- Pharmacy portal login is per-user and read-only ("View Only" role); only the session token is
  cached, never the password.
