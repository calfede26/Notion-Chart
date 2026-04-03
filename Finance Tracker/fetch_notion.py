import os
import json
import requests

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = "2b242ff37a05803fb633fc6ef749d575"

MONTH_ORDER = {
    "Settembre 25": 1,
    "Ottobre 25": 2,
    "Novembre 25": 3,
    "Dicembre 25": 4,
    "Gennaio 26": 5,
    "Febbraio 26": 6,
    "Marzo 26": 7,
}

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def query_database():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    results = []
    has_more = True
    start_cursor = None

    while has_more:
        body = {}
        if start_cursor:
            body["start_cursor"] = start_cursor
        resp = requests.post(url, headers=headers, json=body)
        resp.raise_for_status()
        data = resp.json()
        results.extend(data["results"])
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return results

def extract_formula_number(prop):
    if not prop:
        return None
    if prop.get("type") == "formula":
        formula = prop["formula"]
        if formula.get("type") == "number":
            return formula.get("number")
    return None

def extract_select(prop):
    if not prop:
        return None
    if prop.get("type") == "select":
        sel = prop.get("select")
        return sel["name"] if sel else None
    return None

pages = query_database()
entries = []

for page in pages:
    props = page["properties"]
    mese = extract_select(props.get("Data"))
    totale_effettivo = extract_formula_number(props.get("Totale effettivo"))
    netto = extract_formula_number(props.get("Netto"))

    if mese and totale_effettivo is not None:
        entries.append({
            "mese": mese,
            "totale_effettivo": round(totale_effettivo, 2),
            "netto": round(netto, 2) if netto is not None else None,
            "order": MONTH_ORDER.get(mese, 99),
        })

entries.sort(key=lambda x: x["order"])

output = {
    "labels": [e["mese"] for e in entries],
    "totale_effettivo": [e["totale_effettivo"] for e in entries],
    "netto": [e["netto"] for e in entries],
}

os.makedirs("Finance Tracker", exist_ok=True)
with open("Finance Tracker/data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Fatto:", json.dumps(output, ensure_ascii=False))
