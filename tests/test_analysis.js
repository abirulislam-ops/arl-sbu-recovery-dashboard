/* Unit tests for src/analysis/analysis.js — run: node tests/test_analysis.js */
const assert = require("assert");
const A = require("../src/analysis/analysis.js");
const fs = require("fs");
const path = require("path");

const DATA = path.join(__dirname, "..", "data");
const pnl = JSON.parse(fs.readFileSync(path.join(DATA, "sbu_pnl.json"), "utf8"));
const summ = JSON.parse(fs.readFileSync(path.join(DATA, "market_share_summary.json"), "utf8"));
const get = (code) => pnl.find((r) => r.sbu === code);

let pass = 0;
const t = (name, fn) => {
  try { fn(); pass++; console.log("  ok   " + name); }
  catch (e) { console.log("  FAIL " + name + " -> " + e.message); process.exitCode = 1; }
};

console.log("§4.1 loss bridge");
t("AIL bridge residual reconciles to the NP gap", () => {
  const b = A.lossBridge(get("AIL"));
  assert(b.npGapCr != null);
  const sum = (b.revenueEffectCr || 0) + (b.marginEffectCr || 0) + (b.residualCr || 0);
  assert(Math.abs(sum - b.npGapCr) < 0.02, "bridge does not reconcile: " + sum + " vs " + b.npGapCr);
});
t("AELOTH bridge reconciles", () => {
  const b = A.lossBridge(get("AELOTH"));
  const sum = (b.revenueEffectCr || 0) + (b.marginEffectCr || 0) + (b.residualCr || 0);
  assert(Math.abs(sum - b.npGapCr) < 0.02);
});
t("AELOTH keeps the contradictory GP% visible, not hidden", () => {
  const p = get("AELOTH");
  const gp = p.revenue - Math.abs(p.cogs);
  assert(gp < 0 && p.gp_pct > 0, "expected the audit contradiction to persist in data");
});

console.log("§4.2 share loss");
const ail = summ.find((s) => s.sbu === "AIL").share_q4_q1;
t("AIL reads Q4 3.05 -> Q1 2.92", () => {
  const s = A.shareLoss(ail);
  assert(s.available);
  assert(Math.abs(s.q4 - 3.05) < 0.01 && Math.abs(s.q1 - 2.92) < 0.01);
  assert(s.dpp < 0 && s.gainer === "AKS");
});
t("SBU without share data returns the gap, not a fake zero", () => {
  const s = A.shareLoss({ ours: null });
  assert.strictEqual(s.available, false);
  assert.strictEqual(s.gap, "C1/C2");
});

console.log("§4.3 7P");
t("unscored 7P reports the open Ps", () => {
  const r = A.sevenPGap([{ p: "Price", own: 369, compValue: 334 }, { p: "Product", own: null, compValue: null }]);
  assert(r.available);
  assert(r.open.includes("Product"));
  assert(r.headline.includes("Price"));
});
t("no rows -> gap F1-F7", () => {
  assert.strictEqual(A.sevenPGap([]).available, false);
});

console.log("§4.4 game");
t("AIL matrix returns 4 cells and a best response", () => {
  const p = get("AIL");
  const g = A.gameMatrix({ q1Eat: p.net_profit, revenue: p.revenue, cmPct: (p.gp_pct || 0) * 100 });
  assert(g.available);
  assert(Object.keys(g.matrix).length === 4);
  assert(["hold", "cut"].includes(g.bestResponse));
});
t("missing inputs -> not computed, illustrative", () => {
  const g = A.gameMatrix({ q1Eat: null, revenue: null, cmPct: null });
  assert.strictEqual(g.available, false);
});

console.log("§4.5 direction");
t("negative margin forces exit review", () => {
  assert.strictEqual(A.direction({ cmPct: -36.6 }).d, "Restructure / Exit review");
});
t("0.13 pp share loss does not trigger fight-for-share", () => {
  assert.notStrictEqual(A.direction({ cmPct: 13.5, shareDpp: -0.13 }).d, "Fight for share");
});
t("0.5 pp share loss triggers fight-for-share", () => {
  assert.strictEqual(A.direction({ cmPct: 13.5, shareDpp: -0.5 }).d, "Fight for share");
});
t("credibility bands", () => {
  assert.strictEqual(A.credibility(100, 100, 4), "Credible");
  assert.strictEqual(A.credibility(60, 100, 8), "Stretch");
  assert.strictEqual(A.credibility(10, 100, null), "Not credible");
});

console.log("§4.6 simulators");
t("breakeven = fixed / CM%", () => assert.strictEqual(A.breakevenSales(10, 20), 50));
t("1 pp share recovery EAT", () => assert.strictEqual(A.shareRecoveryEat(1000, 1, 15), 1.5));
t("allocator ranks by EAT per Cr and respects the budget", () => {
  const out = A.allocate(50, [
    { sbu: "A", eatRecoveredCr: 30, costCr: 20 },
    { sbu: "B", eatRecoveredCr: 20, costCr: 40 },
  ]);
  assert.strictEqual(out[0].sbu, "A");
  assert(out.reduce((s, x) => s + x.spendCr, 0) <= 50);
});

console.log("\n" + pass + " tests passed");
