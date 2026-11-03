/* Compute the MD headline for every loss-making SBU from the analysis modules.
 * Run: node scripts/headlines.js   (prints only; nothing is rendered or written)
 */
const fs = require("fs");
const path = require("path");
const A = require("../src/analysis/analysis.js");

const DATA = path.join(__dirname, "..", "data");
const read = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));

const pnl = read("sbu_pnl.json");
const dirs = read("sbu_direction.json");
const summ = read("market_share_summary.json");
const seven = read("seven_p.json");

const shareFor = (code) => {
  const s = summ.find((x) => x.sbu === code && x.share_q4_q1);
  return s ? s.share_q4_q1 : null;
};

const rows = pnl
  .slice()
  .sort((a, b) => (a.net_profit ?? 0) - (b.net_profit ?? 0))
  .map((p) => {
    const bridge = A.lossBridge(p);
    const share = A.shareLoss(shareFor(p.sbu));
    const p7 = A.sevenPGap(
      seven.filter((r) => r.sbu === p.sbu).map((r) => ({ p: r.p, own: r.own_q1, compValue: null })),
      p.sbu === "AIL" ? "rebar" : "default"
    );
    const cred = A.credibility(p.commit_rev, p.deficit, null);
    const d = dirs.find((x) => x.sbu === p.sbu) || {};
    const dir = A.direction({ cmPct: (p.gp_pct ?? 0) * 100, shareDpp: share.available ? share.dpp : null, bridge, credibility: cred });
    const bits = [];
    bits.push(`${p.name}: Q1 EAT ${p.net_profit?.toFixed(2)} Cr, revenue ${(p.revenue / (p.budget_revenue || 1) * 100).toFixed(0)}% of budget.`);
    if (bridge?.npGapCr != null) bits.push(`Budget-to-actual gap ${bridge.npGapCr.toFixed(2)} Cr, of which ${bridge.revenueEffectCr != null ? bridge.revenueEffectCr.toFixed(2) : "-"} Cr is revenue shortfall at actual margin (${bridge.class} driver).`);
    if (share.available) bits.push(share.headline);
    else bits.push(`Market share not available (gap ${share.gap}).`);
    if (p7.available) bits.push(p7.headline);
    bits.push(`Direction: ${dir.d}; plan credibility ${cred}.`);
    return { sbu: p.sbu, name: p.name, headline: bits.join(" "), bridge, share, p7, dir, cred };
  });

for (const r of rows) {
  console.log("\n== " + r.sbu + " — " + r.name);
  console.log(r.headline);
}
