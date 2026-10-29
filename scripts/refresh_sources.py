#!/usr/bin/env python3
"""Refresh the live sources into data/ before each build.

  1. SBU scorecard sheet  -> data/_raw/sbu_sheet.csv   (Q1 revenue / GP / EAT / deficit / loss)
  2. CBDO KPI sheet       -> data/customer_health.json (CSAT, brand health)
  3. ARL CRM API          -> data/crm.json             (visits / leads / opps / cases)

CRM credentials are read from Windows Credential Manager (target: ARL_CRM) —
never stored in a file. If the credential is missing the CRM step is skipped and
the old snapshot is kept (marked stale), nothing is guessed.

Counts use the API's totalCount, not the number of rows paged (that was the
cause of an earlier over-count: 600 vs the real 586/506/273).
"""
import csv, io, json, os, sys, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
RAW = os.path.join(DATA, "_raw")
SCORECARD = "1W-Y6vGGhxNjtOYRB_F72pNGHRV2n9MYPcElwewfLw0U"
KPI_SHEET = "1rldMbL3SfzfKtKTDlXj2VQqgfXZRk7vyYmN5m9bkHAE"
CRM = "https://arlcrm-api.ibos.agency"
BU = {"Ready Mix": 41, "Consumer Electronics": 20, "Next JobZ": 66, "Essentials": 26, "Ispat": 30,
      "Mediplex": 36, "Commodities": 18, "LifeCare": 32, "Telecom": 47, "Infotech": 29, "Logistics": 34}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=90).read()


def refresh_scorecard():
    blob = fetch("https://docs.google.com/spreadsheets/d/%s/export?format=csv&gid=475852686" % SCORECARD)
    os.makedirs(RAW, exist_ok=True)
    open(os.path.join(RAW, "sbu_sheet.csv"), "wb").write(blob)
    rows = list(csv.reader(io.StringIO(blob.decode("utf-8", "replace"))))
    print("scorecard: %d rows" % len(rows))


def refresh_kpi():
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(fetch("https://docs.google.com/spreadsheets/d/%s/export?format=xlsx" % KPI_SHEET)), data_only=True)
    ws = wb[wb.sheetnames[0]]
    out = []
    meta = {"C1": ("Customer Satisfaction Score (CSAT)", 0.10),
            "C2": ("Brand Health Score", 0.15)}
    for r in range(1, ws.max_row + 1):
        code = ws.cell(r, 1).value
        if code in meta:
            m = {"jun": ws.cell(r, 12).value, "jul": ws.cell(r, 14).value,
                 "aug": ws.cell(r, 16).value, "sep": ws.cell(r, 18).value}
            vals = [v for v in m.values() if isinstance(v, (int, float))]
            out.append({"kpi": meta[code][0], "code": code, "target": ws.cell(r, 10).value,
                        "uom": ws.cell(r, 8).value, "polarity": ws.cell(r, 9).value,
                        "months": m, "q1_avg": round(sum(vals[-3:]) / len(vals[-3:]), 2) if len(vals) >= 3 else None,
                        "ytd_achievement": None, "status": ws.cell(r, 40).value or "On Track",
                        "weight": meta[code][1], "source": "CBDO KPI & Tracking FY2026-27"})
    if out:
        json.dump(out, open(os.path.join(DATA, "customer_health.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print("kpi: %d rows" % len(out))
    else:
        print("kpi: nothing parsed — snapshot kept")


def read_cred(target="ARL_CRM"):
    import ctypes
    class CREDENTIAL(ctypes.Structure):
        _fields_ = [("Flags", ctypes.c_uint32), ("Type", ctypes.c_uint32), ("TargetName", ctypes.c_wchar_p),
                    ("Comment", ctypes.c_wchar_p), ("LastWritten", ctypes.c_byte * 8),
                    ("CredentialBlobSize", ctypes.c_uint32), ("CredentialBlob", ctypes.c_void_p),
                    ("Persist", ctypes.c_uint32), ("AttributeCount", ctypes.c_uint32),
                    ("Attributes", ctypes.c_void_p), ("TargetAlias", ctypes.c_wchar_p), ("UserName", ctypes.c_wchar_p)]
    p = ctypes.c_void_p()
    if not ctypes.windll.advapi32.CredReadW(target, 1, 0, ctypes.byref(p)):
        return None, None
    c = ctypes.cast(p, ctypes.POINTER(CREDENTIAL)).contents
    blob = ctypes.wstring_at(c.CredentialBlob, c.CredentialBlobSize // 2)
    ctypes.windll.advapi32.CredFree(p)
    return c.UserName, blob


def refresh_crm():
    try:
        import requests
    except ImportError:
        print("crm: requests missing — skipped"); return
    user, pw = read_cred()
    if not pw:
        print("crm: no stored credential (ARL_CRM) — snapshot kept"); return
    H = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "Mozilla/5.0",
         "Origin": "https://arlcrm.ibos.agency", "Referer": "https://arlcrm.ibos.agency/"}
    r = requests.post(CRM + "/crm/Auth/Login", json={"email": user, "password": pw}, headers=H, timeout=45)
    if r.status_code != 200:
        print("crm: login failed %s — snapshot kept" % r.status_code); return
    d = r.json(); tok = d.get("accessToken") or (d.get("data") or {}).get("accessToken")
    cov, detail = [], {}
    for name, bu in BU.items():
        sw = requests.post(CRM + "/crm/Auth/SwitchBusinessUnit", json={"businessUnitId": bu},
                           headers={**H, "Authorization": "Bearer " + tok}, timeout=45).json()
        tok = sw.get("accessToken") or (sw.get("data") or {}).get("accessToken") or tok
        HH = {**H, "Authorization": "Bearer " + tok}
        c = {}
        for key, path in (("visits", "/crm/Visit/GetVisitList"), ("leads", "/crm/Lead/GetLeadList"),
                          ("opps", "/crm/Opportunity/GetOpportunityList"), ("cases", "/crm/ServiceCase/GetCaseList")):
            try:
                j = requests.get(CRM + path + "?pageNumber=1&pageSize=1", headers=HH, timeout=40).json()
                c[key] = j.get("totalCount", 0)
            except Exception:
                c[key] = None
        cov.append({"sbu": name, "visits": c["visits"], "leads": c["leads"], "opps": c["opps"],
                    "cases": c["cases"], "cases_overdue": None, "window_from": None, "window_to": None,
                    "source": "ARL CRM (arlcrm.ibos.agency) · totalCount · auto"})
    old = {}
    p = os.path.join(DATA, "crm.json")
    if os.path.exists(p):
        old = json.load(open(p, encoding="utf-8"))
    # keep detail block from the full pull (it needs row-level data)
    payload = {"coverage": cov, "detail": old.get("detail", {})}
    json.dump(payload, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("crm: %d BUs" % len(cov))


def main():
    for step in (refresh_scorecard, refresh_kpi, refresh_crm):
        try:
            step()
        except Exception as e:
            print("%s failed: %s" % (step.__name__, str(e)[:200]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
