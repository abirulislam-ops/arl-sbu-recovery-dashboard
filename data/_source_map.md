# Source map — Data ID → source → status

Period: Q1 FY2026-27 (Jul–Sep 2026) · BDT Cr · as of 2026-10-28

| Data ID | Item | Source found | Status | Owner | Freshness |
|---|---|---|---|---|---|
| A1 | SBU P&L (Q1) | Scorecard sheet + ERP GL | OK (Q1) | Finance | auto |
| A2 | Revenue bridge inputs | ERP GL revenue + oms orders | Partial (no qty/price split) | Finance/Sales Ops | auto |
| A3 | SKU profitability | — | MISSING | Finance | — |
| A4 | Profit per dealer/region | — | MISSING | Finance | — |
| A5 | Trade spend & schemes | GL 4210001 (total only) | Partial | Marketing/Finance | auto |
| A6 | RM & production cost | mes cost sheet | Partial | Supply Chain | — |
| A7 | Logistics cost | GL 4410001 + order freight | Partial | Logistics | auto |
| A8 | Budget vs actual | Scorecard sheet | OK | Finance | auto |
| A9 | Fixed cost & break-even | ALL SE dashboard (9 BUs) | Partial (2 of 12 SBUs) | Finance | auto |
| B1 | Dealer master | prt.tblBusinessPartner | Partial (thana on 17% of partners) | Sales Ops | auto |
| B2 | Dealer monthly lifting | oms orders | Partial (7 SBUs) | Sales Ops | auto |
| B3 | Active dealer count | oms orders (derived) | Partial (7 SBUs) | Sales Ops | auto |
| B4 | Lost dealers | oms orders (derived) | Partial (7 SBUs, 622 dealers) | Sales Ops | auto |
| B5 | Declining dealers | oms orders (derivable) | Partial | Sales Ops | — |
| B6 | New dealers | first order date | Partial | Sales Ops | — |
| B7 | Credit & receivables | fin AR | Partial | Credit Control | — |
| B8 | Unfulfilled orders | oms vs delivery | Partial | Supply Chain | — |
| B9 | Complaints/claims | ARL CRM service cases (5) | Partial (Ready Mix only) | QA | auto |
| C1 | Market size by region | Marketing files: Cement + Ready Mix national | Partial (2 of 8) | Marketing Data Head | auto |
| C2 | Competitor volume by region | Marketing files (brand volumes) | Partial (national only) | Marketing Data Head | auto |
| C3 | Own volume (market definition) | — | MISSING | Sales Ops | — |
| C4 | Dealer share-of-wallet | — | MISSING | Sales | — |
| C5 | Distribution coverage | rtm outlet + Retail Outlet file | Partial | Marketing | auto |
| D1 | Org structure & vacancies | PeopleDesk DB (72 tables) | Available — not yet pulled | HR | mcp |
| D2 | KPI target vs achievement | hr/kpi-target-achievement | Available — not yet pulled | Sales Ops | mcp |
| D3 | CRM call & visit log | ARL CRM API | Delivered — but empty for Q1 (22 visits, all Oct-26) | Sales Ops/IT | auto |
| D4 | Last contact with lost dealers | ARL CRM API | Delivered — no Q1 records exist | Sales Ops/IT | auto |
| D5 | Beat compliance | rtm tour plan + sitevisit | Available — not yet pulled | Sales Ops | mcp |
| D6 | Attrition & transfers | PeopleDesk DB | Available — not yet pulled | HR | mcp |
| E1 | Competitor price list | Ready Mix benchmark (ASP by brand) | Partial (1 SBU) | Sales/Marketing | auto |
| E2 | Competitor offers | — | MISSING | Sales | — |
| E3 | Lost dealer → competitor | — | MISSING | Sales | — |
| F1 | 7P — own vs competitor | Ready Mix 7P file | Partial (1 SBU, 3 of 7 P evidenced) | Marketing | auto |
| F4 | Promotion (own) | Brand pack ATL/BTL mix | Partial | Marketing | auto |
| G2 | Stock-outs | wms stock + movement | Available — not yet pulled | Supply Chain | mcp |
| G3 | OTIF | oms order vs delivery | Available — not yet pulled | Supply Chain | mcp |
| H1 | Dealer exit interviews | — | MISSING | Sales | — |
| I1 | Macro events | SBU root-cause notes (qualitative) | Partial | Strategy | manual |
| P1 | People cost by SBU | PeopleDesk payroll via ctc-mcp | OK | HR / Finance | auto |
| P2 | CSAT & brand health | CBDO KPI sheet | OK | Marketing | auto |
| P3 | Product portfolio (BCG) | Marketing market-share file | Partial (Essentials only) | Marketing Data Head | auto |

**IT Data Link Tracker:** column K (Data Link) is empty for all 54 rows and all link statuses read
'Pending' / 'Not checked'. No IT file has been shared yet — the tracker confirms the MISSING items above.

**Note:** DWH (203.202.241.211) was unreachable on 2026-10-28, so fin/oms DWH mirrors could not be used.