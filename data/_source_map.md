# Source map — Data ID → source → status

Period: Q1 FY2026-27 (Jul–Sep 2026) · BDT Cr · as of 2026-11-01

| Data ID | Item | Source found | Status | Owner | Freshness |
|---|---|---|---|---|---|
| A1 | SBU P&L (Q1) | Scorecard sheet + ERP GL | OK (Q1) | Finance | auto |
| A2 | Revenue bridge inputs | ERP GL revenue + oms.tblSalesOrderRow (numOrderQuantity × numItemPrice) | OK | Finance/Sales Ops | mcp |
| A3 | SKU profitability | BOM × pro price (mfg) + cost sheet (Ready Mix) + purchase (resale) + service cost (TMS/OMS) | OK — 12 SBUs: SKU count + GP/CM% + cost path | Finance | mcp |
| A4 | Profit per dealer/region | oms.tblSalesOrderHeader + fin.tblAccountingJournal + oms.tblDistributorPerfromanceScore | Partial (scorecard Oct-25 only) | Finance | mcp |
| A5 | Trade spend & schemes | GL 4210001 + region dimension (join partner district) | Partial | Marketing/Finance | auto |
| A6 | RM & production cost | mes.tblBillOfMaterialHeader + tblCostSheetHeader + pro.tblPurchaseOrderRow | Partial (conversion cost needs MOH config) | Supply Chain | mcp |
| A7 | Logistics cost | GL 4410001 + sms.tblDeliveryHeader/Row | Partial | Logistics | auto |
| A8 | Budget vs actual | bgt.tblBudgetIncomeExpenseHeader + Row (FY 26-27) + scorecard | OK | Finance | mcp |
| A9 | Fixed cost & break-even | fin GL 4110001/4510001/4610001 | OK (all SBUs) | Finance | mcp |
| B1 | Dealer master | prt.tblBusinessPartner + BusinessPartnerTerritory → rtm.tblTerritoryInfo (district) | OK — district 57%→71% (2,804 filled via territory join) | IT / Sales Ops | mcp |
| B2 | Dealer monthly lifting | oms orders | Partial (7 SBUs) | Sales Ops | auto |
| B3 | Active dealer count | oms orders (derived) | Partial (7 SBUs) | Sales Ops | auto |
| B4 | Lost dealers | oms orders (derived) | Partial (7 SBUs, 622 dealers) | Sales Ops | auto |
| B5 | Declining dealers | oms orders (derivable) | Partial | Sales Ops | — |
| B6 | New dealers | first order date + oms.TblCustomerAcquisitionHeader | Partial | Sales Ops | — |
| B7 | Credit & receivables | fin.tblAccountingJournal (GL 1120001 AR) | OK | Credit Control | mcp |
| B8 | Unfulfilled orders | oms.tblSalesOrderRow numUndeliveryValues (Q1-scoped) | OK — Ispat 65.4 · Ready Mix 41.3 · Essentials 18.1 Cr short | Supply Chain | mcp |
| B9 | Complaints/claims | prt.tblSiteComplainInfo + tblSiteComplainInfoDetails | Partial (Ready Mix only) | QA | auto |
| C1 | Market size by region | Marketing Google Sheet — national: Ispat 56→105 Lac t, Ready Mix 85 Mn cft, Essentials rice/flour, Asphalt, Logistics | OK (national; regional split = field) | Marketing Data Head | sheet |
| C2 | Competitor volume by region | Marketing Google Sheet — share tables (Ispat, Ready Mix) + Logistics sea-export share (Maersk 9.99% · KN 8.38% · MGH 7.41% · DSV 6.12%) + competitor lists | OK (national share; regional = field) | Marketing Data Head | sheet |
| C3 | Own volume (market definition) | oms.tblSalesOrderRow → market UOM (MT/m³/pieces) via net-weight | OK — 8 SBUs: own volume in market unit | Sales Ops | mcp |
| C4 | Dealer share-of-wallet | Marketing Google Sheet — market-level benchmark (Ispat 3.5% SOW, Ready Mix) | Partial (benchmark known; per-dealer survey pending) | Sales | sheet |
| C5 | Distribution coverage | rtm outlet + Marketing outlet distribution (Essentials 175k, Ispat region table) + Logistics customer/shipper lists | Partial | Marketing | sheet |
| D1 | Org structure & vacancies | peopledesk_arl/saas.empEmployeeBasicInfo | Pulled (19,008 employees) | HR | mcp |
| D2 | KPI target vs achievement | oms.tblCustomerSalesTargetHeader + tblManpowerSalesTarget | Pulled (Essentials 32,194 · Ispat 5,753) | Sales Ops | mcp |
| D3 | CRM call & visit log | oms.tblViciDialApiCallLog + tblCustomerVisit | Delivered — empty for Q1 (last call 28-Aug-2025) | Sales Ops/IT | mcp |
| D4 | Last contact with lost dealers | oms.tblViciDialFeedBack | Delivered — no Q1 records (last 15-Nov-2025) | Sales Ops/IT | mcp |
| D5 | Beat compliance | rtm.tblRoutePlanHeader + tblTourPlanHeader | Pulled (Essentials 6,695 routes) | Sales Ops | mcp |
| D6 | Attrition & transfers | saas.empEmployeeSeparation + empTransferNPromotion | Pulled (2,248 sep · 76 transfers) | HR | mcp |
| E1 | Competitor price list | Marketing Google Sheet — Logistics Nov carrier rates + master SKU price list (xlsx), Ispat EX Mill/NSP, Essentials SKU, Mediplex lab, Ready Mix rates | OK (multi-SBU) | Sales/Marketing | sheet |
| E2 | Competitor offers | oms.tblCompetitorPriceHeader + Marketing sheet (Logistics financing/credit schemes, Ispat mill/transport/landing, Ready Mix customer offers) | Partial (Logistics + Essentials + Ispat + Ready Mix + Cement) | Sales | sheet |
| E3 | Lost dealer → competitor | oms.tblCompetitor (list) + Marketing competitor mapping (Mediplex) | Partial (competitor lists per SBU; per-dealer mapping = field survey) | Sales | sheet |
| F1 | 7P — own vs competitor | Marketing Google Sheet — Logistics full 7P (xlsx), Essentials (7P full) + Ispat (7P + weighted) + Mediplex | OK (Logistics + Essentials + Ispat) | Marketing | sheet |
| F4 | Promotion (own) | Marketing Google Sheet — Logistics GL 4210001 by region + Ispat + Ready Mix budget | Partial (3 SBUs budget) | Marketing | sheet |
| G2 | Stock-outs | wms.tblInventoryTransactionHeader | Pulled (3.16M txns, 7 loss SBUs) | Supply Chain | mcp |
| G3 | OTIF / fill rate | sms.tblDeliveryHeader (on-time) + oms value (fill) · UOM set per SBU | OK — on-time 95–100% · fill 73–100% | Supply Chain | mcp |
| H1 | Dealer exit interviews | oms.tblViciDialFeedBack (call-center feedback) | Partial (118 rows, none in Q1) | Sales | mcp |
| I1 | Macro events | SBU root-cause notes (qualitative) | Partial | Strategy | manual |
| P1 | People cost by SBU | PeopleDesk payroll via ctc-mcp | OK | HR / Finance | auto |
| P2 | CSAT & brand health | CBDO KPI sheet | OK | Marketing | auto |
| P3 | Product portfolio (BCG) | Marketing market-share file | Partial (Essentials only) | Marketing Data Head | auto |

**Audit re-check 2026-11-01 (DB schema reference + live verification):**
- Recovered 4 MISSING → Partial: A3 (SKU cost via BOM), A4 (profit/dealer via oms+fin+scorecard), H1 (exit interview via ViciDial feedback — but no Q1 rows), C3 (own volume via oms.tblSalesOrderRow).
- Upgraded 3 Partial → OK: A2 (qty×price in oms row), A9 (fixed cost in fin GL, all SBUs), B7 (AR GL 1120001).
- Improved 4 Partial (better source, still partial): A5 (region dim), A6 (BOM added), A7 (delivery rows), B9 (prt complain tables).
- Recovered E2 (competitor offers) → Partial: oms.tblCompetitorPriceHeader + Row has numAvgMarketOffer/numDP/numTP/numMRP for Essentials + Ispat + Cement (2024-25).
- Still MISSING (not in DB for the loss SBUs): C4 (dealer share-of-wallet — cement-only survey + binary "Exclusive" flag), E3 (lost dealer → competitor — farm feed-only registry).
- New DB sources found but not yet tracked as Data IDs: LC/payables (com.tblLetterOfCredit 2,694), downtime (mes.tblNPTHeader), quality/rejection (mes.tblQualityCheckHeader), incentive (sms.tblIncentiveConfigHeader + tblEmployeeIncentive), training (hcm.tblTraining). Budget now DB-backed (bgt, FY 26-27 all 14 SBUs).

**IT Data Link Tracker:** column K (Data Link) is empty for all 54 rows and all link statuses read 'Pending' / 'Not checked'. No IT file has been shared yet — the tracker confirms the MISSING items above.

**Note:** DWH (203.202.241.211) was unreachable on 2026-10-28, so fin/oms DWH mirrors could not be used.
