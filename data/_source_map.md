# Source map — Data ID → source → status

Period: Q1 FY2026-27 (Jul–Sep 2026) · BDT Cr · as of 2026-10-29

| Data ID | Item | Source found | Status | Owner | Freshness |
|---|---|---|---|---|---|
| A1 | SBU P&L | Google Sheet + ERP GL (monthly cost split) | OK | Finance | 2026-10-29 |
| A2 | Revenue bridge inputs | ERP GL revenue + oms orders (qty/price) | Partial (revenue + net price) | Finance/Sales Ops | 2026-10-29 |
| A3 | SKU profitability | mes.tblCostSheetHeader+Row | Partial (Ready Mix only) | Finance | 2026-10-29 |
| A4 | Profit per dealer/region | oms orders (dealer/region revenue only) | Partial (revenue, not profit) | Finance | 2026-10-29 |
| A5 | Trade spend & schemes | ERP GL 4210001 | OK | Marketing/Finance | 2026-10-29 |
| A6 | RM & production cost | mes cost sheet + pro PO row | Partial | Supply Chain | 2026-10-29 |
| A7 | Logistics cost | ERP GL 4410001 | OK | Logistics | 2026-10-29 |
| A8 | Budget vs actual | Google Sheet | OK (revenue/EAT) | Finance | Q1 |
| A9 | Fixed cost & break-even | ALL SE dashboard | Partial (2 of 12 SBUs) | Finance | Oct MTD |
| B1 | Dealer master | prt.tblBusinessPartner (13 BUs) | OK | Sales Ops | 2026-10-29 |
| B2 | Dealer monthly lifting | oms orders (customer × month) | Partial | Sales Ops | 2026-10-29 |
| B3 | Active dealer count | ERP sales orders | Partial (13 BUs) | Sales Ops | 2026-10-29 |
| B4 | Lost dealers | ERP sales orders | Partial (7 SBUs, count only) | Sales Ops | 2026-10-29 |
| B5 | Declining dealers | ERP sales orders (decline > 0) | Partial | Sales Ops | 2026-10-29 |
| B6 | New dealers | ERP sales orders (new customers) | Partial | Sales Ops | 2026-10-29 |
| B7 | Credit & receivables | fin AR GL 1120001 + credit limits | Partial | Credit Control | 2026-10-29 |
| B8 | Unfulfilled orders | oms open orders | Partial | Supply Chain | 2026-10-29 |
| B9 | Complaints/claims | prt.tblSiteComplainInfo | Partial | QA | 2026-10-29 |
| C1 | Market size by region | — | MISSING | Marketing/Strategy | — |
| C2 | Competitor volume by region | — | MISSING | Marketing/Strategy | — |
| C3 | Own volume (market definition) | — | MISSING | Sales Ops | — |
| C4 | Dealer share-of-wallet | — | MISSING | Sales | — |
| C5 | Distribution coverage | — | MISSING | Marketing | — |
| D1 | Org structure & vacancies | PeopleDesk (separate system) | MISSING | HR/Sales Ops | — |
| D2 | KPI target vs achievement | oms.tblKPITarget + customer sales target | Partial | Sales Ops | 2026-10-29 |
| D3 | CRM call & visit log | oms.tblSiteVisit (only iBOS BU) | MISSING (not in ERP for 14 SBUs) | Sales Ops/IT | — |
| D4 | Last contact with lost dealers | — | MISSING | Sales Ops/IT | — |
| D5 | Beat compliance | rtm.tblTourPlanHeader | Partial | Sales Ops | 2026-10-29 |
| D6 | Attrition & transfers | PeopleDesk (separate system) | MISSING | HR | — |
| E1 | Competitor price list | — | MISSING | Sales/Marketing | — |
| E2 | Competitor offers | — | MISSING | Sales | — |
| E3 | Lost dealer → competitor | — | MISSING | Sales | — |
| F4 | Promotion (own) | Brand pack ATL/BTL mix | Partial | Marketing | FY plan |
| G2 | Stock-outs | — | MISSING | Supply Chain | — |
| G3 | OTIF | sms.tblDeliveryHeader (delivery data) | Partial (on-time % pending) | Supply Chain | 2026-10-29 |
| H1 | Dealer exit interviews | — | MISSING | Sales | — |
| I1 | Macro events | SBU root-cause notes (qualitative) | Partial | Strategy | Q1 |

**IT Data Link Tracker (updated 2026-10-29):** 26 data items now have a live ERP table source and were
pulled. Items still MISSING fall into three buckets: (1) market/competitor research (Marketing C1–C5, E1–E3)
— external, not in ERP; (2) PeopleDesk HR data (D1, D6) — separate system; (3) surveys/manual (D4, G2, H1).
The CRM visit log (D3) exists only for iBOS BU — the 14 loss SBUs never used it, so it is confirmed absent.
