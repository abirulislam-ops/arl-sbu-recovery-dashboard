# Source map — Data ID → source → status

Period: Q1 FY2026-27 (Jul–Sep 2026) · BDT Cr · as of 2026-11-01

| Data ID | Item | Source found | Status | Owner | Freshness |
|---|---|---|---|---|---|
| A1 | SBU P&L (Q1) | Scorecard sheet + ERP GL | OK (Q1) | Finance | auto |
| A2 | Revenue bridge inputs | ERP GL revenue + oms.tblSalesOrderRow (numOrderQuantity × numItemPrice) | OK | Finance/Sales Ops | mcp |
| A3 | SKU profitability | mes.tblBillOfMaterialHeader + tblCostSheetHeader (4 mfg SBUs) + pro.tblPurchaseOrderRow (resale) | Partial (mfg SBUs only) | Finance | mcp |
| A4 | Profit per dealer/region | oms.tblSalesOrderHeader + fin.tblAccountingJournal + oms.tblDistributorPerfromanceScore | Partial (scorecard Oct-25 only) | Finance | mcp |
| A5 | Trade spend & schemes | GL 4210001 + region dimension (join partner district) | Partial | Marketing/Finance | auto |
| A6 | RM & production cost | mes.tblBillOfMaterialHeader + tblCostSheetHeader + pro.tblPurchaseOrderRow | Partial (conversion cost needs MOH config) | Supply Chain | mcp |
| A7 | Logistics cost | GL 4410001 + sms.tblDeliveryHeader/Row | Partial | Logistics | auto |
| A8 | Budget vs actual | bgt.tblBudgetIncomeExpenseHeader + Row (FY 26-27) + scorecard | OK | Finance | mcp |
| A9 | Fixed cost & break-even | fin GL 4110001/4510001/4610001 | OK (all SBUs) | Finance | mcp |
| B1 | Dealer master | prt.tblBusinessPartner | Partial (thana on 17% of partners) | Sales Ops | auto |
| B2 | Dealer monthly lifting | oms orders | Partial (7 SBUs) | Sales Ops | auto |
| B3 | Active dealer count | oms orders (derived) | Partial (7 SBUs) | Sales Ops | auto |
| B4 | Lost dealers | oms orders (derived) | Partial (7 SBUs, 622 dealers) | Sales Ops | auto |
| B5 | Declining dealers | oms orders (derivable) | Partial | Sales Ops | — |
| B6 | New dealers | first order date + oms.TblCustomerAcquisitionHeader | Partial | Sales Ops | — |
| B7 | Credit & receivables | fin.tblAccountingJournal (GL 1120001 AR) | OK | Credit Control | mcp |
| B8 | Unfulfilled orders | oms undelivered value (pulled) | Pulled — value shows a unit error (Essentials 93,745 Cr vs 555 Cr revenue) | Supply Chain | mcp |
| B9 | Complaints/claims | prt.tblSiteComplainInfo + tblSiteComplainInfoDetails | Partial (Ready Mix only) | QA | auto |
| C1 | Market size by region | Marketing files: Cement + Ready Mix national | Partial (2 of 8) | Marketing Data Head | auto |
| C2 | Competitor volume by region | Marketing files (brand volumes) | Partial (national only) | Marketing Data Head | auto |
| C3 | Own volume (market definition) | — | MISSING | Sales Ops | — |
| C4 | Dealer share-of-wallet | — | MISSING | Sales | — |
| C5 | Distribution coverage | rtm outlet + Retail Outlet file | Partial | Marketing | auto |
| D1 | Org structure & vacancies | PeopleDesk DB (72 tables) | Available — not yet pulled | HR | mcp |
| D2 | KPI target vs achievement | hr/kpi-target-achievement | Available — not yet pulled | Sales Ops | mcp |
| D3 | CRM call & visit log | oms.tblViciDialApiCallLog + tblCustomerVisit | Delivered — empty for Q1 (last call 28-Aug-2025) | Sales Ops/IT | mcp |
| D4 | Last contact with lost dealers | oms.tblViciDialFeedBack | Delivered — no Q1 records (last 15-Nov-2025) | Sales Ops/IT | mcp |
| D5 | Beat compliance | rtm tour plan + sitevisit | Available — not yet pulled | Sales Ops | mcp |
| D6 | Attrition & transfers | PeopleDesk DB | Available — not yet pulled | HR | mcp |
| E1 | Competitor price list | Ready Mix benchmark (ASP by brand) | Partial (1 SBU) | Sales/Marketing | auto |
| E2 | Competitor offers | — | MISSING | Sales | — |
| E3 | Lost dealer → competitor | — | MISSING | Sales | — |
| F1 | 7P — own vs competitor | Ready Mix 7P file | Partial (1 SBU, 3 of 7 P evidenced) | Marketing | auto |
| F4 | Promotion (own) | Brand pack ATL/BTL mix | Partial | Marketing | auto |
| G2 | Stock-outs | wms stock + movement | Available — not yet pulled | Supply Chain | mcp |
| G3 | OTIF / fill rate | oms order vs delivered qty (pulled) | Pulled — qty is mixed UOM (MT/bag/pc), % not usable yet | Supply Chain | mcp |
| H1 | Dealer exit interviews | oms.tblViciDialFeedBack (call-center feedback) | Partial (118 rows, none in Q1) | Sales | mcp |
| I1 | Macro events | SBU root-cause notes (qualitative) | Partial | Strategy | manual |
| P1 | People cost by SBU | PeopleDesk payroll via ctc-mcp | OK | HR / Finance | auto |
| P2 | CSAT & brand health | CBDO KPI sheet | OK | Marketing | auto |
| P3 | Product portfolio (BCG) | Marketing market-share file | Partial (Essentials only) | Marketing Data Head | auto |

**Audit re-check 2026-11-01 (DB schema reference + live verification):**
- Recovered 3 MISSING → Partial: A3 (SKU cost via BOM), A4 (profit/dealer via oms+fin+scorecard), H1 (exit interview via ViciDial feedback — but no Q1 rows).
- Upgraded 3 Partial → OK: A2 (qty×price in oms row), A9 (fixed cost in fin GL, all SBUs), B7 (AR GL 1120001).
- Improved 4 Partial (better source, still partial): A5 (region dim), A6 (BOM added), A7 (delivery rows), B9 (prt complain tables).
- Still MISSING (Marketing-owned, not in DB): C3, C4, E2, E3.
- New DB sources found but not yet tracked as Data IDs: LC/payables (com.tblLetterOfCredit 2,694), downtime (mes.tblNPTHeader), quality/rejection (mes.tblQualityCheckHeader), incentive (sms.tblIncentiveConfigHeader + tblEmployeeIncentive), training (hcm.tblTraining). Budget now DB-backed (bgt, FY 26-27 all 14 SBUs).

**IT Data Link Tracker:** column K (Data Link) is empty for all 54 rows and all link statuses read 'Pending' / 'Not checked'. No IT file has been shared yet — the tracker confirms the MISSING items above.

**Note:** DWH (203.202.241.211) was unreachable on 2026-10-28, so fin/oms DWH mirrors could not be used.
