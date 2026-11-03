"""Restore the rich dashboard and integrate the new analysis pages into it.

Old file: index.rich.html (the live build before the cockpit rebuild)
Adds:     Loss Bridge, Competitive Game, Simulator  (+ share Q4->Q1 on Market Share)
Keeps:    everything the MD had before (SBU narratives, demarcation, CRM, CSAT,
          people, BCG, brand audit, campaigns, links, data status)
"""
import re

BASE = r"C:\Users\wajeehan computer\Documents\Default Project\arl-sbu-recovery-dashboard"
src = BASE + r"\index.rich.html"
dst = BASE + r"\index.html"

html = open(src, encoding="utf-8-sig").read()

# 1. keep the cockpit build for reference
open(BASE + r"\index.cockpit.html", "w", encoding="utf-8", newline="").write(
    open(BASE + r"\index.html", encoding="utf-8-sig").read())

# 2. new panes right after the data pane
pane_anchor = '<section id="pane-data" class="pane"></section>'
if pane_anchor in html:
    html = html.replace(pane_anchor, pane_anchor +
        '\n      <section id="pane-loss" class="pane"></section>'
        '\n      <section id="pane-game" class="pane"></section>'
        '\n      <section id="pane-sim" class="pane"></section>', 1)

# 3. register the pages
html = re.sub(r"const FIXED_PAGES=\[[^\]]*\]",
              "const FIXED_PAGES=['md','overview','market','sales','rootcause','loss','game','sim','data']",
              html, count=1)

# 4. nav entries
nav_anchor = 'data-t="data"'
i = html.find(nav_anchor)
if i > 0:
    end = html.find("</button>", i) + len("</button>")
    extra = ('<button class="menu-item" data-t="loss" title="Budget to actual loss bridge"><span class="serial">\u25a4</span>'
             '<span class="dot" style="background:#dc2626"></span><span class="nm">Loss Bridge</span></button>\n'
             '    <button class="menu-item" data-t="game" title="2x2 payoff vs the main gainer"><span class="serial">\u25c8</span>'
             '<span class="dot" style="background:#4f46e5"></span><span class="nm">Competitive Game</span></button>\n'
             '    <button class="menu-item" data-t="sim" title="Price, volume and COGS simulator"><span class="serial">\u25b3</span>'
             '<span class="dot" style="background:#0891b2"></span><span class="nm">Simulator</span></button>')
    html = html[:end] + "\n    " + extra + html[end:]

# 5. render functions, inserted before the footer function
render_js = r"""
/* ---- Loss Bridge / Competitive Game / Simulator ---- */
function mdRows(){
  return (MD.pnl||[]).slice().sort((a,b)=>(b.loss||0)-(a.loss||0)).map(p=>{
    const rev=p.revenue||0, bRev=p.budget_revenue||0, gp=(p.gp_pct||0)*100;
    const revEff=(bRev-rev)*gp/100;
    const gap=(p.budget_np!=null&&p.net_profit!=null)?p.budget_np-p.net_profit:null;
    const resid=gap!=null?gap-revEff:null;
    return {p,revEff,gap,resid,driver:(gap!=null&&Math.abs(revEff)>=Math.abs(gap)*0.5)?'market':'internal'};
  });
}
function renderLoss(){
  const rows=mdRows();
  const max=Math.max(...rows.map(r=>Math.abs(r.p.loss||0)),1);
  const body=rows.map(r=>`<tr>
    <td><b>${r.p.name}</b><div class="code">${r.p.sbu}</div></td>
    <td class="num" style="color:#b91c1c">${(r.p.loss||0).toFixed(2)}</td>
    <td><div style="background:#fee2e2;border-radius:4px;min-width:120px"><div style="width:${Math.abs(r.p.loss||0)/max*100}%;height:9px;background:#dc2626;border-radius:4px"></div></div></td>
    <td class="num">${r.gap==null?'\u2014':r.gap.toFixed(2)}</td>
    <td class="num">${r.revEff.toFixed(2)}</td>
    <td class="num">${r.resid==null?'\u2014':r.resid.toFixed(2)}</td>
    <td><span class="vtag ${r.driver==='market'?'verdict-P':'verdict-I'}">${r.driver}</span></td></tr>`).join('');
  const tot=rows.reduce((s,r)=>s+(r.p.loss||0),0);
  document.getElementById('pane-loss').innerHTML=`
    <div class="sec-head"><span class="bar" style="background:#dc2626"></span><div><h2>Where the ${tot.toFixed(2)} Cr went</h2><p>Q1 EAT loss by SBU, and the budget-to-actual gap split into revenue shortfall vs everything else.</p></div></div>
    <div class="card"><div style="overflow-x:auto"><table class="mini">
      <thead><tr><th>SBU</th><th class="num">Q1 EAT</th><th>Loss</th><th class="num">NP gap</th><th class="num">Revenue effect</th><th class="num">Residual</th><th>Driver</th></tr></thead>
      <tbody>${body}</tbody></table></div>
      <div class="src">Revenue effect = (budget revenue \u2212 actual) \u00d7 actual GP%. Residual = cost, finance and mix \u2014 not decomposed because budget GP% and unit data are missing.</div></div>
    <div class="dec-rec" style="margin-top:12px"><b>So what \u2192 Direction \u2192 Decision.</b> ${rows.filter(r=>r.driver==='market').length} of ${rows.length} SBUs are market-driven: price or volume, not cost. Those are the ones where a share or pricing decision can move money this quarter.</div>`;
}
function gameCell(rev,cogs,eat,pMove,theirCut){
  const el=-1.2, match=0.6;
  const vol=1+(pMove*el)/100;
  const rel=1+(pMove-(theirCut?-5*match:0))/100;
  const cm=(rev-Math.abs(cogs||0))/rev;
  return (rev*vol*cm*rel - rev*vol*cm) + eat;
}
function renderGame(){
  const body=(MD.pnl||[]).map(p=>{
    const rev=p.revenue||0, cogs=p.cogs||0, eat=p.net_profit||0;
    const hh=gameCell(rev,cogs,eat,0,false), hc=gameCell(rev,cogs,eat,0,true);
    const ch=gameCell(rev,cogs,eat,-5,false), cc=gameCell(rev,cogs,eat,-5,true);
    const best=Math.max(hh,hc)>=Math.max(ch,cc)?'hold':'cut';
    const cell=(v,eq)=>`<td class="num" style="${eq?'background:#eff6ff;font-weight:800;border:1px solid #93c5fd':''}">${v.toFixed(2)}</td>`;
    return `<tr><td><b>${p.name}</b><div class="code">${p.sbu}</div></td>
      ${cell(hh,best==='hold')}${cell(hc,false)}${cell(ch,false)}${cell(cc,best==='cut')}
      <td><span class="vtag ${best==='hold'?'verdict-C':'verdict-P'}">${best==='hold'?'hold price':'cut price'}</span></td></tr>`;
  }).join('');
  document.getElementById('pane-game').innerHTML=`
    <div class="sec-head"><span class="bar" style="background:#4f46e5"></span><div><h2>Competitive game \u2014 our move vs the main gainer</h2><p>Payoff in BDT Cr EAT for the quarter. Highlighted cell = best response.</p></div></div>
    <div class="card"><div style="overflow-x:auto"><table class="mini">
      <thead><tr><th>SBU</th><th class="num">We hold / they hold</th><th class="num">We hold / they cut</th><th class="num">We cut / they hold</th><th class="num">We cut / they cut</th><th>Best</th></tr></thead>
      <tbody>${body}</tbody></table></div>
      <div class="src">Illustrative: price elasticity \u22121.2, rival matches 60% of any cut. Replace with observed elasticities when available.</div></div>
    <div class="dec-rec" style="margin-top:12px"><b>So what \u2192 Direction \u2192 Decision.</b> Commodity SBUs (cement, rebar, RMC) sit in a price-war structure: cutting first moves EAT down for everyone. Hold price and compete on delivery and credit where the rival is weakest.</div>`;
}
function renderSim(){
  const opts=(MD.pnl||[]).map(p=>`<option value="${p.sbu}">${p.name}</option>`).join('');
  document.getElementById('pane-sim').innerHTML=`
    <div class="sec-head"><span class="bar" style="background:#0891b2"></span><div><h2>Simulator</h2><p>Defaults are Q1 actuals. Move a slider to see the EAT effect.</p></div></div>
    <div class="card">
      <div class="mdb-top"><span class="tag">SBU <select id="simSbu" style="border:0;background:transparent;font:inherit;font-weight:700">${opts}</select></span></div>
      <div style="display:grid;gap:6px;margin:8px 0">
        <label style="font-size:12px">Price change <input id="simP" type="range" min="-15" max="15" value="0" step="1"> <b id="simPV">0%</b></label>
        <label style="font-size:12px">Volume change <input id="simV" type="range" min="-30" max="30" value="0" step="1"> <b id="simVV">0%</b></label>
        <label style="font-size:12px">COGS change <input id="simC" type="range" min="-15" max="15" value="0" step="1"> <b id="simCV">0%</b></label>
      </div>
      <div class="grid g4">
        <div class="sbustat"><div class="l">New EAT</div><div class="v" id="simEat">\u2014</div></div>
        <div class="sbustat"><div class="l">Pickup</div><div class="v" id="simDelta">\u2014</div></div>
        <div class="sbustat"><div class="l">Break-even sales</div><div class="v" id="simBe">\u2014</div></div>
      </div>
      <div class="src">EAT = revenue \u00d7 (1+price) \u00d7 (1+volume) \u2212 COGS \u00d7 (1+cost) \u00d7 (1+volume) + other income and fixed costs held at Q1 level.</div>
    </div>`;
  const run=()=>{
    const code=document.getElementById('simSbu').value;
    const p=(MD.pnl||[]).find(x=>x.sbu===code); if(!p) return;
    const dp=+document.getElementById('simP').value, dv=+document.getElementById('simV').value, dc=+document.getElementById('simC').value;
    document.getElementById('simPV').textContent=dp+'%';document.getElementById('simVV').textContent=dv+'%';document.getElementById('simCV').textContent=dc+'%';
    const rev=(p.revenue||0)*(1+dp/100)*(1+dv/100);
    const cogs=Math.abs(p.cogs||0)*(1+dc/100)*(1+dv/100);
    const other=(p.net_profit||0)-((p.revenue||0)-Math.abs(p.cogs||0));
    const eat=rev-cogs+other;
    document.getElementById('simEat').textContent=eat.toFixed(2)+' Cr';
    document.getElementById('simDelta').textContent=(eat-(p.net_profit||0)>=0?'+':'')+(eat-(p.net_profit||0)).toFixed(2)+' Cr';
    const cm=(rev-cogs)/rev;
    document.getElementById('simBe').textContent=(cm>0&&other<0)?(-other/cm).toFixed(1)+' Cr':'\u2014';
  };
  ['simSbu','simP','simV','simC'].forEach(id=>{const e=document.getElementById(id); if(e){e.oninput=run; e.onchange=run;}});
  run();
}
"""
anchor = "function renderFooter(){"
html = html.replace(anchor, render_js + "\n" + anchor, 1)

# 6. init calls
html = re.sub(r"renderMD\(\);renderMarket\(\);",
              "renderMD();renderMarket();renderLoss();renderGame();renderSim();", html, count=1)
if "renderLoss();" not in html:
    html = html.replace("renderMenu();", "renderMenu();\nrenderLoss();renderGame();renderSim();", 1)

open(dst, "w", encoding="utf-8", newline="").write(html)
print("restored rich dashboard with 3 new pages; bytes:", len(html))
