/* Pure analysis functions — skill §4.1–4.6.
 * No DOM, no data loading here: every function takes plain objects and returns
 * plain objects, so it can be unit-tested (tests/test_analysis.js).
 * Money in BDT Cr, shares in %, deltas in pp.
 */

const cr = (x) => (x == null ? null : Math.round(x * 100) / 100);
const pp = (x) => (x == null ? null : Math.round(x * 100) / 100);

/** §4.1 loss bridge. Uses what the scorecard actually gives us.
 *  revenueEffect = (actual revenue − budget revenue) × actual GP%
 *  marginEffect  = revenue × (actual GP% − budget GP%) when a budget GP% exists
 *  rest          = cost / finance / other, taken as the residual and labelled
 */
function lossBridge(p, budgetGpPct = null) {
  if (!p || p.revenue == null) return null;
  const rev = p.revenue;
  const bRev = p.budget_revenue;
  const gpp = p.gp_pct != null ? p.gp_pct * 100 : null;
  const revenueEffect = bRev != null && gpp != null ? cr((bRev - rev) * gpp / 100) : null;
  const marginEffect = budgetGpPct != null && gpp != null ? cr(rev * (gpp - budgetGpPct) / 100) : null;
  const npGap = p.budget_np != null && p.net_profit != null ? cr(p.budget_np - p.net_profit) : null;
  const explained = (revenueEffect || 0) + (marginEffect || 0);
  const residual = npGap != null ? cr(npGap - explained) : null;
  return {
    npGapCr: npGap, revenueEffectCr: revenueEffect, marginEffectCr: marginEffect,
    residualCr: residual,
    residualLabel: "cost / finance / other (residual — not decomposed yet)",
    class: npGap == null ? "unknown" : (Math.abs(revenueEffect || 0) >= Math.abs(npGap) * 0.5 ? "market" : "internal"),
    confidence: budgetGpPct == null ? "low — budget GP% missing" : "medium",
  };
}

/** §4.2 share loss. row = {q4_share, q1_share, delta_pp, top_gainer:{company,delta_pp}} */
function shareLoss(row) {
  if (!row || row.ours == null) {
    return { available: false, gap: "C1/C2", headline: null };
  }
  const o = row.ours, g = row.top_gainer || {};
  const d = o.delta_pp;
  const dir = d < -0.05 ? "lost" : d > 0.05 ? "gained" : "held";
  return {
    available: true, q4: o.q4_share, q1: o.q1_share, dpp: d, direction: dir,
    gainer: g.company || null, gainerPp: g.delta_pp == null ? null : g.delta_pp,
    mechanism: "unknown — no price/offer evidence for this SBU (gap E1/E2)",
    headline: `${dir === "lost" ? "We lost" : dir === "gained" ? "We gained" : "We held"} ${Math.abs(d).toFixed(2)} pp share Q4→Q1` +
      (o.q1_share != null ? ` (now ${o.q1_share.toFixed(2)}%)` : "") +
      (g.company ? `, while ${g.company} moved ${g.delta_pp > 0 ? "+" : ""}${g.delta_pp.toFixed(2)} pp` : "") + ".",
  };
}

/** §4.3 7P gap. rows = [{p, own, compValue, status}], weights per industry. */
const P_WEIGHTS = {
  rebar: { Price: 0.35, Place: 0.25, Product: 0.15, People: 0.1, Process: 0.08, Promotion: 0.04, "Physical evidence": 0.03 },
  default: { Price: 0.2, Place: 0.2, Product: 0.15, People: 0.15, Process: 0.1, Promotion: 0.1, "Physical evidence": 0.1 },
};

function sevenPGap(rows, industry = "default") {
  if (!rows || !rows.length) return { available: false, gap: "F1-F7", headline: "7P not scored for this SBU." };
  const w = P_WEIGHTS[industry] || P_WEIGHTS.default;
  const scored = rows.filter((r) => r.own != null && r.compValue != null);
  const gaps = scored.map((r) => ({ p: r.p, gap: r.compValue - r.own, weight: w[r.p] || 0.1 }))
    .map((g) => ({ ...g, score: g.gap * g.weight }))
    .sort((a, b) => b.score - a.score);
  const open = rows.filter((r) => r.own == null || r.compValue == null).map((r) => r.p);
  const worst = gaps[0];
  return {
    available: gaps.length > 0, gaps, open,
    headline: worst
      ? `We lose on ${worst.p} (${worst.gap > 0 ? "-" : "+"}${Math.abs(worst.gap).toFixed(1)}); fix ${worst.p} first.` +
        (open.length ? ` ${open.length} of 7 P not scored.` : "")
      : `7P not scored — gap ${open.join(", ")}.`,
  };
}

/** §4.4 game: 2x2 hold/cut price vs one rival, payoff in BDT Cr EAT.
 *  Assumption stated: price elasticity e (volume % per 1% price change) and
 *  rival reaction share (how much of our price move the rival matches).
 */
function gameMatrix(input) {
  const { q1Eat, revenue, cmPct, elasticity = -1.2, rivalMatch = 0.6 } = input;
  if (q1Eat == null || !revenue || cmPct == null) {
    return { available: false, headline: "Game not computed — CM% or revenue missing.", illustrative: true };
  }
  const cell = (ourCut, theirCut) => {
    const pMove = ourCut ? -5 : 0;
    const volOur = 1 + (pMove * elasticity) / 100;
    const relPrice = 1 + (pMove - (theirCut ? -5 * rivalMatch : 0)) / 100;
    const eat = revenue * volOur * (cmPct / 100) * relPrice - (revenue * volOur * (cmPct / 100)) + q1Eat;
    return cr(eat);
  };
  const m = {
    usHold_themHold: cell(false, false), usHold_themCut: cell(false, true),
    usCut_themHold: cell(true, false), usCut_themCut: cell(true, true),
  };
  const bestIfHold = Math.max(m.usHold_themHold, m.usHold_themCut);
  const bestIfCut = Math.max(m.usCut_themHold, m.usCut_themCut);
  const best = bestIfHold >= bestIfCut ? "hold" : "cut";
  return {
    available: true, matrix: m, bestResponse: best,
    structure: "Prisoner's dilemma / price war (commodity)",
    assumption: `price elasticity ${elasticity}, rival matches ${Math.round(rivalMatch * 100)}% of our cut`,
    headline: `Best response: ${best === "hold" ? "hold price" : "cut price"} — EAT ${cr(best === "hold" ? bestIfHold : bestIfCut)} Cr vs ${cr(best === "hold" ? bestIfCut : bestIfHold)} Cr. Illustrative.`,
  };
}

/** §4.5 direction rules, applied in order, with the evidence that triggered it. */
function direction(x) {
  const { cmPct, shareDpp, bridge, credibility } = x;
  if (cmPct == null) return { d: "Restructure / Exit review", why: "CM% unknown and gross margin thin — cannot prove the unit earns anything", conf: "low" };
  if (cmPct <= 0) return { d: "Restructure / Exit review", why: `gross margin ${cmPct.toFixed(1)}% — every extra taka of sales adds loss`, conf: "high" };
  if (shareDpp != null && shareDpp <= -0.25) return { d: "Fight for share", why: `share fell ${Math.abs(shareDpp).toFixed(2)} pp Q4→Q1`, conf: "medium" };
  if (credibility === "Credible" && (bridge?.class || "").startsWith("market")) return { d: "Fix & Recover", why: "loss is market-driven and the plan closes the gap", conf: "medium" };
  if (cmPct < 10) return { d: "Harvest (cash, not share)", why: `thin ${cmPct.toFixed(1)}% margin — protect cash, stop buying volume`, conf: "medium" };
  return { d: "Reposition / niche", why: "margin is workable but the volume/price position is not", conf: "low" };
}

/** §4.5 plan credibility: commit vs deficit and break-even date vs Q2. */
function credibility(commit, deficit, beMonths) {
  if (deficit == null || deficit <= 0) return "Not applicable";
  const cov = commit == null ? 0 : (commit / deficit) * 100;
  if (cov >= 90 && (beMonths == null || beMonths <= 6)) return "Credible";
  if (cov >= 50) return "Stretch";
  return "Not credible";
}

/** §4.6 simulators. */
function breakevenSales(fixedCr, cmPct) {
  if (!fixedCr || !cmPct || cmPct <= 0) return null;
  return cr(fixedCr / (cmPct / 100));
}
function shareRecoveryEat(marketCr, ppGain, cmPct) {
  if (marketCr == null || !ppGain || cmPct == null) return null;
  return cr(marketCr * (ppGain / 100) * (cmPct / 100));
}
function allocate(totalCr, sbus) {
  return sbus
    .filter((s) => s.eatRecoveredCr > 0 && s.costCr > 0)
    .map((s) => ({ sbu: s.sbu, perCr: s.eatRecoveredCr / s.costCr, ...s }))
    .sort((a, b) => b.perCr - a.perCr)
    .reduce((acc, s) => {
      if (totalCr <= 0) return acc;
      const spend = Math.min(totalCr, s.costCr);
      acc.push({ sbu: s.sbu, spendCr: cr(spend), eatCr: cr(spend * s.perCr) });
      totalCr -= spend;
      return acc;
    }, []);
}

module.exports = { lossBridge, shareLoss, sevenPGap, gameMatrix, direction, credibility,
  breakevenSales, shareRecoveryEat, allocate, P_WEIGHTS };
