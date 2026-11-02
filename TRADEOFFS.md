# Tradeoffs & decisions — 2026-11-02

> Context for anyone (or any agent) touching this dashboard afterwards. These are the
> deliberate choices made while integrating the Marketing Google Sheet data, and **why**.
> Do not silently revert these labels — if you think one is wrong, read the "why" first.

## The 4-state data model (replaces ~10 ad-hoc labels)

Every data item is now classified into exactly one of four states, which answer one question:
**"is this settled, or who do I chase?"**

| State | Meaning | Action |
|---|---|---|
| **Delivered** | we have the number + source | stop — done |
| **Not Applicable** | the data does not exist for this SBU (reason attached) | stop — do not chase |
| **Pending** | it exists / is producible, owner hasn't supplied it yet | chase the owner |
| **Blocked** | it needs a source that isn't connected (feed stopped, link broken) | escalate the blocker |

**Why:** the Marketing team's sheets used ~10 overlapping labels (`DATA REQUIRED`, `MISSING`,
`Partial`, `TEMPLATE`, `COMMENT`, `N/A`, `CONTEXT`, `PENDING`, …) that conflated "this data
doesn't exist" with "we're still chasing it". An employee's comment ("Mediplex has no dealer
partnership") is the **reason**, not a status — it goes *inside* "Not Applicable".

## Specific decisions

1. **Regional market size / competitor volume (C1/C2) = "Not Applicable".**
   Nobody publishes market size or competitor volume *by region and by quarter* (a quarter that
   closed weeks ago). The "Diagnosis by SBU" only needs the **national** answer (did the market
   shrink, or did we lose share). Own volume by region (C3) is still in the DB. Marking regional
   C1/C2 "Not Applicable" stops the team chasing phantom data.

2. **National "market size" for 6 service/niche SBUs = "Not Applicable".**
   Commodities, LifeCare, Mediplex, Telecom, Next JobZ, Infotech have **no published national
   market-size figure** for their category. This is a fact, not a gap.

3. **Asphalt own 7P scores = "Pending" (not "Not Applicable").**
   Unlike the above, this *is* producible — the team can self-score in minutes. Owner = Asphalt
   marketing. (They have said they will update it.)

4. **The `!` badge is now dynamic — it fires on "Blocked" only.**
   No more hard-coded `!`. It is computed from the source map: a tab shows `!` only when its
   Data IDs have a `MISSING`/`EMPTY` (blocked) status. Result today: Market Share has no `!`
   (settled); Sales KPI shows `!` because its D3/D4 CRM call-log feed is genuinely stopped
   (ViciDial, last entry 28-Aug-2025). When IT restarts that feed, the `!` clears by itself.

5. **CRM "went live after Q1" = "Problem → solution", not an error.**
   The CRM only has records from October 2026 (after Q1 closed), so "did we call the lost
   dealers in Q1?" is unanswerable from CRM/iBOS. This was reframed from a red "Brutal fact"
   box to a neutral "Problem → solution" note (solution: dealer exit interviews H1), and the
   dealer-churn data we *do* have (7 SBUs) is shown; the rest is zero.

6. **"Diagnosis by SBU" is "National" (final), not "proxy".**
   Since regional is Not Applicable, the national diagnosis (own revenue Q4→Q1 vs national
   market growth) **is** the final answer — no longer labeled a stand-in.

7. **Market-share data now comes from the Marketing Google Sheet (not the old brand pack).**
   Ispat (BSRM 33%, Akij 3.5%), Ready Mix (Shah 22.8%, Akij 11.2%), Logistics sea-export
   (Maersk 9.99% · KN 8.38% · MGH 7.41%) — these replaced the earlier "brand pack" proxies.
   Essentials rice/flour and others remain from the market-share file.

## Source-map Data-ID naming (for the helper tooltips)

- **A** = finance (A1 P&L … A9 fixed cost) · **B** = dealers (B1 master … B9 complaints)
- **C** = market (C1 size, C2 competitor volume, C3 own volume, C4 share-of-wallet, C5 distribution)
- **D** = sales ops (D1 org, D2 KPI, D3/D4 CRM call/visit log, D5 beat, D6 attrition)
- **E** = competitor (E1 price, E2 offers, E3 lost-dealer→competitor) · **F** = marketing (F1 7P, F4 promotion)
- **G** = supply chain (G2 stock-out, G3 OTIF) · **H1** = exit interviews · **I1** = macro · **P** = people/portfolio
