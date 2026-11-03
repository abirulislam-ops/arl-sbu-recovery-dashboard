/* Build the MD decision cockpit (skill §5/§6) into a single index.html.
 * Usage: node scripts/build_cockpit.js
 * Reads data/*.json, uses src/analysis/analysis.js (tested), writes index.html.
 * The previous file is copied to index.prev.html for rollback.
 */
const fs = require("fs");
const path = require("path");
const A = require("../src/analysis/analysis.js");

const BASE = path.join(__dirname, "..");
const DATA = path.join(BASE, "data");
const read = (f, d = []) => {
  try { return JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8")); } catch (e) { return d; }
};

const pnl = read("sbu_pnl.json");
const dirs = read("sbu_direction.json");
const decisions = read("decisions.json");
const hyp = read("hypotheses.json");
const summ = read("market_share_summary.json");
const seven = read("seven_p.json");
const bcg = read("bcg.json");
const audit = read("brand_audit.json");
const crm = read("crm.json");
const health = read("customer_health.json");
const people = read("people.json");
const churn = read("dealer_churn.json");
const regional = read("regional_logistics.json");
const links = read("source_links.json");
const sourceMap = read("_source_map.md", null);

const ORDER = ["AELOTH", "AIL", "ARMCL", "AMPL", "ACL", "ALCL", "ABSLASP", "ATL", "NJL", "AITL", "ACEL", "ALL"];
const n = (x) => (x == null ? "—" : Number(x).toLocaleString("en-US", { maximumFractionDigits: 2 }));
const cr = (x) => (x == null ? "—" : x.toFixed(2));
const pct = (x) => (x == null ? "—" : (x * 100).toFixed(1) + "%");

function shareFor(code) {
  const s = summ.find((x) => x.sbu === code && x.share_q4_q1);
  return s ? s.share_q4_q1 : null;
}
function p7For(code) {
  const rows = seven.filter((r) => r.sbu === code).map((r) => ({ p: r.p, own: r.own_q1, compValue: null }));
  return A.sevenPGap(rows, code === "AIL" ? "rebar" : "default");
}

/* ---------- components ---------- */
const css = `
:root{--ink:#0f172a;--muted:#64748b;--muted2:#94a3b8;--line:#e2e8f0;--line2:#f1f5f9;--bg:#f6f8fb;--card:#fff;
--red:#b91c1c;--redbg:#fef2f2;--amber:#b45309;--amberbg:#fffbeb;--green:#166534;--greenbg:#f0fdf4;--blue:#1d4ed8;--bluebg:#eff6ff}
*{box-sizing:border-box}
body{margin:0;font:13px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg);
font-variant-numeric:tabular-nums}
.app{display:flex;min-height:100vh}
.side{width:236px;flex:none;background:#0b1220;color:#cbd5e1;position:sticky;top:0;height:100vh;overflow:auto;padding:14px 10px}
.brand{display:flex;gap:9px;align-items:center;padding:6px 8px 14px}
.logo{width:30px;height:30px;border-radius:8px;background:linear-gradient(135deg,#6366f1,#8b5cf6);display:grid;place-items:center;color:#fff;font-weight:800}
.brand b{color:#fff;font-size:13px;display:block}
.brand span{font-size:10.5px;color:#8a97a8}
.nav button{display:flex;gap:8px;width:100%;text-align:left;border:0;background:none;color:#9aa7b6;padding:8px 10px;border-radius:8px;font:inherit;font-size:12.5px;cursor:pointer}
.nav button:hover{background:rgba(255,255,255,.06);color:#fff}
.nav button.on{background:linear-gradient(135deg,#6366f1,#4338ca);color:#fff}
.nav .grp{font-size:9.5px;text-transform:uppercase;letter-spacing:.08em;color:#64748b;padding:12px 10px 4px;font-weight:700}
.nav .code{font-size:10px;color:#93a4b8}
.main{flex:1;min-width:0}
header{padding:16px 22px;background:#fff;border-bottom:1px solid var(--line);display:flex;gap:14px;flex-wrap:wrap;align-items:center;justify-content:space-between}
h1{margin:0;font-size:19px;letter-spacing:-.01em}
.kicker{font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--muted2);font-weight:700}
.chips{display:flex;gap:7px;flex-wrap:wrap}
.chip{font-size:11px;background:var(--line2);border:1px solid var(--line);border-radius:99px;padding:4px 10px;color:var(--muted)}
.chip b{color:var(--ink)}
main{padding:18px 22px 60px;max-width:1240px;margin:0 auto}
.page{display:none}.page.on{display:block}
h2{font-size:15px;margin:0}
p.sub{color:var(--muted);font-size:11.5px;margin:2px 0 0}
.sec{margin:20px 0 8px;display:flex;gap:9px;align-items:flex-start}
.sec .bar{width:3px;height:18px;border-radius:2px;background:var(--ink);margin-top:2px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.grid{display:grid;gap:10px}
.g4{grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.kpi .l{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted2);font-weight:700}
.kpi .v{font-size:21px;font-weight:800;margin-top:2px;letter-spacing:-.02em}
.kpi .s{font-size:11px;color:var(--muted);margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted2);text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);font-weight:800}
td{padding:7px 8px;border-bottom:1px solid var(--line2);vertical-align:top}
tr.hl td{background:var(--bluebg)}
td.r,th.r{text-align:right;white-space:nowrap}
.neg{color:var(--red)}.pos{color:var(--green)}.amb{color:var(--amber)}
.tag{display:inline-block;font-size:10px;font-weight:800;padding:2px 7px;border-radius:99px;white-space:nowrap}
.t-fix{background:var(--greenbg);color:var(--green)}.t-fight{background:var(--bluebg);color:var(--blue)}
.t-niche{background:#f5f3ff;color:#5b21b6}.t-harvest{background:var(--amberbg);color:var(--amber)}
.t-exit{background:var(--redbg);color:var(--red)}.t-na{background:var(--line2);color:var(--muted)}
.t-open{background:var(--amberbg);color:var(--amber)}
.note{font-size:10.5px;color:var(--muted2);margin-top:6px}
.headline{font-size:13.5px;font-weight:700;background:#fff;border-left:3px solid var(--ink);padding:9px 12px;border-radius:0 8px 8px 0;margin:8px 0}
.matrix{display:grid;grid-template-columns:1fr 1fr;gap:6px;max-width:520px}
.mcell{border:1px solid var(--line);border-radius:8px;padding:8px;font-size:11px;background:#fff}
.mcell.eq{border-color:var(--blue);box-shadow:0 0 0 2px var(--bluebg)}
.slider{display:flex;gap:10px;align-items:center;font-size:11.5px;margin:6px 0}
.slider input{flex:1}
.sim{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:8px}
.foot{margin-top:26px;font-size:10.5px;color:var(--muted2)}
details{border:1px solid var(--line);border-radius:10px;padding:8px 12px;background:#fff;margin-top:8px}
summary{cursor:pointer;font-size:12px;font-weight:700}
@media(max-width:900px){.app{display:block}.side{width:auto;height:auto;position:relative}.nav{max-height:42vh;overflow:auto}}
`;

const tag = (d) => {
  const map = { "Fix & Recover": "t-fix", "Fight for share": "t-fight", "Reposition / niche": "t-niche",
    "Harvest (cash, not share)": "t-harvest", "Restructure / Exit review": "t-exit" };
  return `<span class="tag ${map[d] || "t-na"}">${d}</span>`;
};

/* ---------- portfolio computations ---------- */
const rows = ORDER.map((code) => {
  const p = pnl.find((x) => x.sbu === code) || {};
  const bridge = A.lossBridge(p);
  const share = A.shareLoss(shareFor(code));
  const p7 = p7For(code);
  const cred = A.credibility(p.commit_rev, p.deficit, null);
  const dir = A.direction({ cmPct: (p.gp_pct || 0) * 100, shareDpp: share.available ? share.dpp : null, bridge, credibility: cred });
  const game = A.gameMatrix({ q1Eat: p.net_profit, revenue: p.revenue, cmPct: (p.gp_pct || 0) * 100 });
  const ch = churn.find((c) => c.sbu === code);
  const pp = people.find((c) => c.sbu === code);
  const ba = audit.find((c) => c.sbu === code);
  const dec = decisions.find((d) => d.sbu === code && d.rank);
  return { code, p, bridge, share, p7, cred, dir, game, ch, pp, ba, dec };
});

const totalLoss = rows.reduce((s, r) => s + (r.p.loss || 0), 0);
const totalDef = rows.reduce((s, r) => s + (r.p.deficit || 0), 0);
const totalCommit = rows.reduce((s, r) => s + (r.p.commit_rev || 0), 0);
const conf = rows.reduce((s, r) => s + (r.p.data_completeness || 0), 0) / rows.length;
const biggest = rows.slice().sort((a, b) => (b.p.loss || 0) - (a.p.loss || 0))[0];
const shareLost = rows.filter((r) => r.share.available && r.share.dpp < 0)[0];
const topDec = decisions.filter((d) => d.rank).sort((a, b) => a.rank - b.rank).slice(0, 3);

/* ---------- pages ---------- */
function mdBrief() {
  const lines = [
    `Biggest bleeder: <b>${biggest.p.name}</b> at <b>${cr(biggest.p.loss)} Cr</b> Q1 EAT, revenue ${pct(biggest.p.revenue / (biggest.p.budget_revenue || 1))} of budget.`,
    shareLost ? `Biggest share loss: <b>${shareLost.p.name}</b> ${Math.abs(shareLost.share.dpp).toFixed(2)} pp to <b>${shareLost.share.gainer}</b> (+${cr(shareLost.share.gainerPp)} pp).`
              : `Market share data exists for <b>1</b> SBU only — the rest is a named gap (C1/C2).`,
    topDec.length ? `The decision that moves the most money: <b>${topDec[0].question}</b> (${cr(topDec[0].options?.[0]?.np_impact_cr)} Cr NP at stake).`
                  : `No decision card carries a quantified NP impact yet.`,
  ];
  const bubbles = rows.map((r, i) => {
    const x = 30 + i * 45;
    const y = 150 - Math.min(120, (r.bridge?.npGapCr || 1) * 6);
    const rad = 6 + Math.sqrt(Math.max(1, r.p.revenue || 1));
    const col = r.dir.d === "Restructure / Exit review" ? "#b91c1c" : r.dir.d === "Fix & Recover" ? "#166534" : "#b45309";
    return `<circle cx="${x}" cy="${y}" r="${Math.min(22, rad)}" fill="${col}" opacity=".35"><title>${r.p.name}: loss ${cr(r.p.loss)} Cr, gap ${cr(r.bridge?.npGapCr)} Cr</title></circle>
      <text x="${x}" y="${y + 3}" font-size="7" text-anchor="middle" fill="#0f172a">${r.code}</text>`;
  }).join("");
  return `<div class="grid g4">
    ${[["Q1 EAT loss", cr(totalLoss) + " Cr", "12 loss-making SBUs"],
       ["Revenue deficit", cr(totalDef) + " Cr", "vs budget"],
       ["Stated commitment", cr(totalCommit) + " Cr", "as written in the recovery plans — includes proposed targets"],
       ["Data confidence", (conf * 100).toFixed(0) + "%", "every verdict is provisional"]]
      .map(([l, v, s]) => `<div class="kpi"><div class="l">${l}</div><div class="v">${v}</div><div class="s">${s}</div></div>`).join("")}
  </div>
  <div class="sec"><span class="bar"></span><div><h2>The answer in 3 lines</h2></div></div>
  <div class="card">${lines.map((l) => `<div class="headline">${l}</div>`).join("")}</div>
  <div class="sec"><span class="bar"></span><div><h2>Loss vs recoverability</h2><p class="sub">x = ND gap, y = size of the fix, bubble = revenue, colour = direction</p></div></div>
  <div class="card"><svg viewBox="0 0 620 170" width="100%" role="img" aria-label="SBU bubble matrix">${bubbles}</svg></div>
  <div class="sec"><span class="bar"></span><div><h2>Top 3 decisions this week</h2></div></div>
  ${topDec.map((d) => `<div class="card" style="margin-bottom:8px"><b>${d.rank}. ${d.question}</b>
     <div style="font-size:11.5px;color:var(--muted);margin-top:3px">${d.brutal_fact}</div>
     <div class="note">NP impact ${cr(d.options?.[0]?.np_impact_cr)} Cr · owner ${d.owner} · decide by ${d.decide_by}</div></div>`).join("")}`;
}

function lossMap() {
  const bars = rows.map((r) => {
    const w = Math.abs(r.p.loss || 0) / Math.max(...rows.map((x) => Math.abs(x.p.loss || 0))) * 100;
    return `<tr><td>${r.p.name}</td><td class="r neg">${cr(r.p.loss)}</td>
      <td><div style="background:var(--redbg);border-radius:4px"><div style="width:${w}%;height:9px;background:#dc2626;border-radius:4px"></div></div></td>
      <td class="r">${cr(r.bridge?.npGapCr)}</td><td class="r">${cr(r.bridge?.revenueEffectCr)}</td>
      <td class="r">${cr(r.bridge?.residualCr)}</td><td>${r.bridge?.class || "—"}</td></tr>`;
  }).join("");
  return `<div class="sec"><span class="bar"></span><div><h2>Where the ${cr(totalLoss)} Cr went</h2><p class="sub">Q1 EAT loss by SBU, and the budget-to-actual gap split into revenue shortfall vs the residual</p></div></div>
  <div class="card"><table><thead><tr><th>SBU</th><th class="r">Q1 EAT</th><th>Loss</th><th class="r">NP gap</th><th class="r">Revenue effect</th><th class="r">Residual</th><th>Driver</th></tr></thead><tbody>${bars}</tbody></table>
  <div class="note">Revenue effect = (budget revenue − actual) × actual GP%. Residual = everything else (cost, finance, mix) — not decomposed because budget GP% and unit data are missing.</div></div>`;
}

function marketPage() {
  const withShare = rows.filter((r) => r.share.available);
  const body = withShare.map((r) => `<tr><td>${r.p.name}</td><td class="r">${cr(r.share.q4)}%</td><td class="r">${cr(r.share.q1)}%</td>
    <td class="r ${r.share.dpp < 0 ? "neg" : "pos"}">${cr(r.share.dpp)} pp</td><td>${r.share.gainer || "—"}</td>
    <td class="r">${cr(r.share.gainerPp)} pp</td><td>${r.share.mechanism}</td></tr>`).join("");
  const gaps = rows.filter((r) => !r.share.available).map((r) => r.p.name).join(", ");
  return `<div class="sec"><span class="bar"></span><div><h2>Who took our share</h2><p class="sub">Q4 FY26 average vs Q1 FY27 average, from the market-share workbook</p></div></div>
  <div class="card">${withShare.length ? `<table><thead><tr><th>SBU</th><th class="r">Q4</th><th class="r">Q1</th><th class="r">Delta</th><th>Top gainer</th><th class="r">Their gain</th><th>How</th></tr></thead><tbody>${body}</tbody></table>` : `<div class="note">No SBU has a parsed share series yet.</div>`}
  <div class="note">Not available (gap C1/C2): ${gaps}. Asphalt is blocked on purpose — the only tab is Lube Oil, which is a different market.</div></div>
  ${regional ? `<div class="sec"><span class="bar"></span><div><h2>Logistics: lane mix vs market</h2></div></div>
  <div class="card"><table><thead><tr><th>Lane</th><th class="r">Our CBM</th><th class="r">Our mix</th><th class="r">Market mix</th><th class="r">Index</th></tr></thead><tbody>
  ${regional.lanes.map((l) => `<tr><td>${l.lane}</td><td class="r">${n(l.own_cbm)}</td><td class="r">${l.own_share_pct}%</td><td class="r">${l.market_share_pct}%</td><td class="r ${l.index >= 1.2 ? "neg" : l.index <= 0.5 ? "amb" : ""}">${l.index}</td></tr>`).join("")}
  </tbody></table><div class="note">${regional.note}</div></div>` : ""}`;
}

function rootCausePage() {
  const split = rows.map((r) => `<tr><td>${r.p.name}</td><td>${r.bridge?.class || "—"}</td><td class="r">${cr(r.bridge?.npGapCr)}</td>
    <td class="r">${cr(r.bridge?.revenueEffectCr)}</td><td class="r">${cr(r.bridge?.residualCr)}</td>
    <td>${churn.find((c) => c.sbu === r.code) ? churn.find((c) => c.sbu === r.code).lost + " dealers lost" : "—"}</td></tr>`).join("");
  const hyps = hyp.map((h) => `<tr><td>${h.id}</td><td>${h.title}</td><td><span class="tag ${h.verdict === "Confirmed" ? "t-fix" : h.verdict === "Partial" ? "t-open" : "t-na"}">${h.verdict}</span></td>
    <td class="r">${h.impact_cr == null ? "—" : cr(h.impact_cr)}</td><td style="max-width:52ch;color:var(--muted)">${(h.evidence || [])[0] || ""}</td></tr>`).join("");
  return `<div class="sec"><span class="bar"></span><div><h2>Market or internal</h2><p class="sub">Driver split from the loss bridge, plus measured dealer churn</p></div></div>
  <div class="card"><table><thead><tr><th>SBU</th><th>Driver</th><th class="r">NP gap</th><th class="r">Revenue effect</th><th class="r">Residual</th><th>Dealer signal</th></tr></thead><tbody>${split}</tbody></table></div>
  <div class="sec"><span class="bar"></span><div><h2>Hypotheses H1 to H9</h2></div></div>
  <div class="card"><table><thead><tr><th>ID</th><th>Hypothesis</th><th>Verdict</th><th class="r">Cr</th><th>First evidence</th></tr></thead><tbody>${hyps}</tbody></table></div>`;
}

function sevenPage() {
  const scored = rows.filter((r) => r.p7.available);
  const all = rows.map((r) => {
    const cells = ["Product", "Price", "Place", "Promotion", "People", "Process", "Physical evidence"].map((p) => {
      const row = seven.find((x) => x.sbu === r.code && x.p === p);
      const v = row && row.own_q1 != null ? row.own_q1 : null;
      return `<td class="r" style="${v == null ? "background:#f8fafc;color:#94a3b8" : ""}">${v == null ? "—" : v}</td>`;
    }).join("");
    return `<tr><td>${r.p.name}</td>${cells}<td>${r.p7.available ? r.p7.headline : '<span class="tag t-open">not scored</span>'}</td></tr>`;
  }).join("");
  return `<div class="sec"><span class="bar"></span><div><h2>7P battlefield</h2><p class="sub">Own Q1 score where evidenced; blank means not scored, never zero</p></div></div>
  <div class="card"><table><thead><tr><th>SBU</th><th class="r">Product</th><th class="r">Price</th><th class="r">Place</th><th class="r">Promotion</th><th class="r">People</th><th class="r">Process</th><th class="r">Physical</th><th>Reading</th></tr></thead><tbody>${all}</tbody></table>
  <div class="note">${scored.length} of ${rows.length} SBUs have any 7P evidence. Weighted gap uses industry weights (rebar: price 0.35, place 0.25).</div></div>`;
}

function gamePage() {
  const cards = rows.map((r) => {
    const g = r.game;
    if (!g.available) return `<div class="card" style="margin-bottom:10px"><b>${r.p.name}</b><div class="note">Not computed — ${g.headline}</div></div>`;
    const m = g.matrix;
    const cell = (v, eq) => `<div class="mcell ${eq ? "eq" : ""}">${cr(v)} Cr</div>`;
    return `<div class="card" style="margin-bottom:10px"><b>${r.p.name}</b> <span class="tag t-na">illustrative</span>
      <div class="note" style="margin:4px 0 8px">${g.headline}</div>
      <div class="matrix">
        <div class="mcell" style="background:#f8fafc;font-weight:700">Us \\ Them</div>
        <div class="mcell" style="background:#f8fafc;font-weight:700">They hold</div>
        <div class="mcell" style="background:#f8fafc;font-weight:700">They cut</div>
        <div class="mcell" style="background:#f8fafc">We hold</div>${cell(m.usHold_themHold, g.bestResponse === "hold")}${cell(m.usHold_themCut, false)}
        <div class="mcell" style="background:#f8fafc">We cut</div>${cell(m.usCut_themHold, false)}${cell(m.usCut_themCut, g.bestResponse === "cut")}
      </div>
      <div class="note">Structure: ${g.structure}. Assumption: ${g.assumption}.</div></div>`;
  }).join("");
  return `<div class="sec"><span class="bar"></span><div><h2>Competitive game</h2><p class="sub">2x2 payoff in BDT Cr EAT — our move vs the main gainer's move</p></div></div>${cards}`;
}

function ddaPage() {
  const body = rows.map((r) => `<tr><td>${r.p.name}</td><td>${tag(r.dir.d)}</td><td style="max-width:34ch">${r.dir.why}</td>
    <td class="r">${cr(r.p.loss)}</td><td>${r.cred}</td><td>${r.dec ? r.dec.owner : "—"}</td><td>${r.dec ? r.dec.decide_by : "—"}</td></tr>`).join("");
  const acts = decisions.filter((d) => d.rank).map((d) => `<tr><td>${d.rank}</td><td>${d.question}</td><td>${d.sbu}</td>
    <td class="r">${cr(d.options?.[0]?.np_impact_cr)}</td><td>${d.owner}</td><td>${d.decide_by}</td><td>${d.tracking_kpi || "—"}</td></tr>`).join("");
  return `<div class="sec"><span class="bar"></span><div><h2>Direction per SBU</h2></div></div>
  <div class="card"><table><thead><tr><th>SBU</th><th>Direction</th><th>Why</th><th class="r">Q1 EAT</th><th>Plan</th><th>Owner</th><th>Decide by</th></tr></thead><tbody>${body}</tbody></table></div>
  <div class="sec"><span class="bar"></span><div><h2>Decisions on the table</h2></div></div>
  <div class="card"><table><thead><tr><th>#</th><th>Decision</th><th>SBU</th><th class="r">NP Cr</th><th>Owner</th><th>By</th><th>KPI</th></tr></thead><tbody>${acts || '<tr><td colspan="7">No ranked decision cards.</td></tr>'}</tbody></table></div>`;
}

function simPage() {
  const opts = rows.map((r) => `<option value="${r.code}">${r.p.name}</option>`).join("");
  return `<div class="sec"><span class="bar"></span><div><h2>Simulator</h2><p class="sub">Defaults are Q1 actuals. Change a slider to see the EAT effect.</p></div></div>
  <div class="card">
    <div class="slider"><span>SBU</span><select id="simSbu" style="flex:1">${opts}</select></div>
    <div class="slider"><span>Price change</span><input id="simPrice" type="range" min="-15" max="15" value="0" step="1"><b id="simPriceV">0%</b></div>
    <div class="slider"><span>Volume change</span><input id="simVol" type="range" min="-30" max="30" value="0" step="1"><b id="simVolV">0%</b></div>
    <div class="slider"><span>COGS change</span><input id="simCogs" type="range" min="-15" max="15" value="0" step="1"><b id="simCogsV">0%</b></div>
    <div class="sim">
      <div class="kpi"><div class="l">New EAT</div><div class="v" id="simEat">—</div></div>
      <div class="kpi"><div class="l">EAT pickup</div><div class="v" id="simDelta">—</div></div>
      <div class="kpi"><div class="l">Break-even sales</div><div class="v" id="simBe">—</div></div>
    </div>
  </div>
  <div class="sec"><span class="bar"></span><div><h2>Portfolio allocator</h2><p class="sub">1 Cr deployed to the SBU with the highest EAT recovered per Cr</p></div></div>
  <div class="card"><table><thead><tr><th>SBU</th><th class="r">EAT per Cr</th><th class="r">Recommended spend</th><th class="r">EAT recovered</th></tr></thead><tbody>
  ${A.allocate(50, rows.map((r) => ({ sbu: r.p.name, eatRecoveredCr: Math.abs(r.p.loss || 0), costCr: Math.abs(r.p.deficit || 1) })))
      .map((x) => `<tr><td>${x.sbu}</td><td class="r">${cr(x.perCr)}</td><td class="r">${cr(x.spendCr)}</td><td class="r">${cr(x.eatCr)}</td></tr>`).join("")}
  </tbody></table></div>`;
}

function sbuPage(r) {
  const s = r.share;
  const g = r.game;
  return `<div class="sec"><span class="bar"></span><div><h2>${r.p.name}</h2><p class="sub">${r.code} · Q1 FY2026-27 · all numbers BDT Cr unless stated</p></div></div>
  <div class="card" style="display:flex;gap:14px;flex-wrap:wrap;align-items:center">
    ${tag(r.dir.d)} <span class="chip">Q1 EAT <b>${cr(r.p.loss)}</b></span>
    <span class="chip">Revenue <b>${pct(r.p.revenue / (r.p.budget_revenue || 1))}</b> of budget</span>
    <span class="chip">Share <b>${s.available ? (s.dpp > 0 ? "+" : "") + cr(s.dpp) + " pp" : "not available"}</b></span>
    <span class="chip">Plan <b>${r.cred}</b></span>
    <span class="chip">Confidence <b>${p21(r.p.data_completeness)}</b></span>
  </div>
  <div class="sec"><span class="bar"></span><div><h2>Where we bleed</h2></div></div>
  <div class="card"><table><tbody>
    <tr><td>Budget revenue</td><td class="r">${cr(r.p.budget_revenue)}</td><td>Actual revenue</td><td class="r">${cr(r.p.revenue)}</td></tr>
    <tr><td>Revenue effect</td><td class="r neg">${cr(r.bridge?.revenueEffectCr)}</td><td>Residual (cost/finance)</td><td class="r">${cr(r.bridge?.residualCr)}</td></tr>
    <tr><td>Budget EAT</td><td class="r">${cr(r.p.budget_np)}</td><td>Actual EAT</td><td class="r neg">${cr(r.p.net_profit)}</td></tr>
  </tbody></table><div class="note">${r.bridge?.confidence || ""}</div></div>
  <div class="sec"><span class="bar"></span><div><h2>Market share</h2></div></div>
  <div class="card">${s.available ? `<div class="headline">${s.headline}</div><div class="note">Mechanism: ${s.mechanism}</div>` : `<div class="note">Not available — gap ${s.gap}. The workbook has no parsed series for this SBU.</div>`}</div>
  <div class="sec"><span class="bar"></span><div><h2>Root cause</h2></div></div>
  <div class="card"><div style="font-size:12.5px">${r.p.root_cause_rev || "Not stated in the scorecard."}</div>
    <div class="note" style="margin-top:8px">Driver: ${r.bridge?.class || "unknown"} · dealer signal: ${r.ch ? r.ch.lost + " of " + r.ch.q4_active + " Q4 dealers stopped buying" : "no order data"}</div></div>
  <div class="sec"><span class="bar"></span><div><h2>7P</h2></div></div>
  <div class="card">${r.p7.available ? `<div class="headline">${r.p7.headline}</div>` : `<div class="note">${r.p7.headline} Gap ${r.p7.gap || "F1-F7"}.</div>`}</div>
  <div class="sec"><span class="bar"></span><div><h2>Competitive game</h2></div></div>
  <div class="card">${g.available ? `<div class="note" style="margin-bottom:6px">${g.headline}</div>
    <div class="matrix"><div class="mcell" style="background:#f8fafc"></div><div class="mcell" style="background:#f8fafc">They hold</div><div class="mcell" style="background:#f8fafc">They cut</div>
    <div class="mcell" style="background:#f8fafc">We hold</div><div class="mcell">${cr(g.matrix.usHold_themHold)}</div><div class="mcell">${cr(g.matrix.usHold_themCut)}</div>
    <div class="mcell" style="background:#f8fafc">We cut</div><div class="mcell">${cr(g.matrix.usCut_themHold)}</div><div class="mcell">${cr(g.matrix.usCut_themCut)}</div></div>
    <div class="note">${g.assumption}</div>` : `<div class="note">${g.headline}</div>`}</div>
  <div class="sec"><span class="bar"></span><div><h2>Direction, decision, action</h2></div></div>
  <div class="card">${tag(r.dir.d)}<div style="font-size:12.5px;margin-top:6px">${r.dir.why}</div>
    ${r.dec ? `<div style="margin-top:8px"><b>${r.dec.question}</b><div class="note">${r.dec.recommendation}</div>
      <div class="note">Owner ${r.dec.owner} · decide by ${r.dec.decide_by} · KPI ${r.dec.tracking_kpi}</div></div>` : `<div class="note">No decision card yet.</div>`}</div>
  <div class="sec"><span class="bar"></span><div><h2>Plan credibility</h2></div></div>
  <div class="card"><b>${r.cred}</b> — commit ${cr(r.p.commit_rev)} Cr vs deficit ${cr(r.p.deficit)} Cr${r.cred === "Not credible" ? " (coverage under half)" : ""}.
    <div class="note">Break-even date not provided by the SBU for this period.</div></div>
  <details><summary>Evidence, people and gaps</summary>
    <div class="note">Brand audit ${r.ba ? r.ba.score_pct + "% (" + r.ba.custodian + ")" : "not audited"} · people ${r.pp ? r.pp.headcount + " staff, CTC " + r.pp.monthly_ctc_cr + " Cr/month" : "n/a"} · CRM visits ${(crm.coverage || []).find((c) => c.sbu === r.p.name)?.visits ?? 0}</div>
  </details>`;
}
const p21 = (x) => (x == null ? "—" : (x * 100).toFixed(0) + "%");

function dataPage() {
  const sm = Array.isArray(sourceMap) ? sourceMap : [];
  const rowsHtml = rows.map((r) => `<tr><td>${r.p.name}</td><td class="r">${pct(r.p.data_completeness)}</td>
    <td>${r.share.available ? "share ok" : "share gap"}</td><td>${r.p7.available ? "7P partial" : "7P gap"}</td>
    <td>${r.cred}</td></tr>`).join("");
  const linkRows = (links.sbus || []).map((s) => `<tr><td>${s.sbu}</td><td class="r">${s.asks}</td><td class="r">${s.linked}</td>
    <td class="r">${(s.rows || []).filter((x) => x.access === "sheet-public" || x.access === "drive-public").length}</td></tr>`).join("");
  return `<div class="sec"><span class="bar"></span><div><h2>Data and sources</h2><p class="sub">Completeness, gaps and the request bookkeeping</p></div></div>
  <div class="card"><table><thead><tr><th>SBU</th><th class="r">Completeness</th><th>Market share</th><th>7P</th><th>Plan</th></tr></thead><tbody>${rowsHtml}</tbody></table></div>
  <div class="sec"><span class="bar"></span><div><h2>Data request links</h2></div></div>
  <div class="card"><table><thead><tr><th>SBU</th><th class="r">Asks</th><th class="r">Linked</th><th class="r">Public</th></tr></thead><tbody>${linkRows}</tbody></table></div>
  <details><summary>Source map (${sm.length} rows)</summary><table><thead><tr><th>ID</th><th>Item</th><th>Source</th><th>Status</th><th>Owner</th></tr></thead><tbody>
    ${sm.map((x) => `<tr><td>${x.id}</td><td>${x.item}</td><td>${x.source}</td><td>${x.status}</td><td>${x.owner}</td></tr>`).join("")}
  </tbody></table></details>
  <div class="foot">Built from data snapshots; every number carries a source file in data/_lineage.json. Missing data is shown as a gap, never estimated.</div>`;
}

/* ---------- assembly ---------- */
const pages = [
  ["md", "MD Brief", mdBrief()],
  ["loss", "Portfolio Loss Map", lossMap()],
  ["market", "Market Share — Who Took It", marketPage()],
  ["root", "Root Cause", rootCausePage()],
  ["seven", "7P Battlefield", sevenPage()],
  ["game", "Competitive Game", gamePage()],
  ["dda", "Direction · Decision · Action", ddaPage()],
  ["sim", "Simulator", simPage()],
  ["data", "Data & Sources", dataPage()],
];

const nav = pages.map(([k, label], i) => `<button data-p="${k}" class="${i === 0 ? "on" : ""}">${label}</button>`).join("") +
  `<div class="grp">Loss-making SBUs</div>` +
  rows.map((r) => `<button data-p="sbu-${r.code}"><span>${r.p.name}</span><span class="code">${r.code}</span></button>`).join("");

const body = pages.map(([k, , html]) => `<section class="page ${k === "md" ? "on" : ""}" id="p-${k}">${html}</section>`).join("") +
  rows.map((r) => `<section class="page" id="p-sbu-${r.code}">${sbuPage(r)}</section>`).join("");

const simData = JSON.stringify(rows.map((r) => ({ code: r.code, rev: r.p.revenue, cogs: r.p.cogs, eat: r.p.net_profit, gpp: r.p.gp_pct })));

const html = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SBU Loss Recovery — MD decision cockpit</title><style>${css}</style></head><body>
<div class="app"><aside class="side"><div class="brand"><div class="logo">A</div><div><b>SBU Loss Recovery</b><span>MD cockpit · Q1 FY2026-27</span></div></div>
<div class="nav">${nav}</div></aside>
<div class="main"><header><div><div class="kicker">AKIJ Resource · Strategic Planning and Analysis</div><h1>Where we bleed, why, and what to decide</h1></div>
<div class="chips"><span class="chip">Q1 <b>Jul–Sep 2026</b></span><span class="chip">SBUs <b>12</b></span>
<span class="chip">Data <b>${(conf * 100).toFixed(0)}%</b></span><span class="chip">As of <b>${new Date().toISOString().slice(0, 10)}</b></span></div></header>
<main>${body}<div class="foot">Single file · no external calls · every figure traceable to data/</div></main></div></div>
<script>
const SIM=${simData};
document.querySelectorAll('.nav button').forEach(b=>b.onclick=()=>{
  document.querySelectorAll('.nav button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
  document.getElementById('p-'+b.dataset.p).classList.add('on');window.scrollTo({top:0});
});
function sim(){
  const code=document.getElementById('simSbu').value;
  const d=SIM.find(x=>x.code===code); if(!d) return;
  const p=+document.getElementById('simPrice').value, v=+document.getElementById('simVol').value, c=+document.getElementById('simCogs').value;
  document.getElementById('simPriceV').textContent=p+'%';document.getElementById('simVolV').textContent=v+'%';document.getElementById('simCogsV').textContent=c+'%';
  const rev=d.rev*(1+p/100)*(1+v/100);
  const cogs=Math.abs(d.cogs||0)*(1+c/100)*(1+v/100);
  const other=(d.eat-(d.rev-Math.abs(d.cogs||0)))||0;
  const eat=rev-cogs+other;
  document.getElementById('simEat').textContent=eat.toFixed(2)+' Cr';
  document.getElementById('simDelta').textContent=(eat-d.eat>=0?'+':'')+(eat-d.eat).toFixed(2)+' Cr';
  const gp=(rev-cogs)/rev;
  document.getElementById('simBe').textContent=(gp>0&&other<0)?(-other/gp).toFixed(1)+' Cr':'n/a';
}
['simSbu','simPrice','simVol','simCogs'].forEach(id=>{const e=document.getElementById(id);if(e)e.oninput=sim;});
if(document.getElementById('simSbu'))sim();
</script></body></html>`;

fs.copyFileSync(path.join(BASE, "index.html"), path.join(BASE, "index.prev.html"));
fs.writeFileSync(path.join(BASE, "index.html"), html, "utf8");
console.log("built index.html", (html.length / 1024).toFixed(0) + " KB", "| pages", pages.length + rows.length);
