import os
import json
import requests
from datetime import datetime

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID  = "2a952343c2ce4155b805b01c3d4c1730"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def fetch_all_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    results = []
    payload = {"sorts": [{"property": "Date", "direction": "ascending"}]}

    while True:
        res = requests.post(url, headers=headers, json=payload)
        res.raise_for_status()
        body = res.json()
        results.extend(body.get("results", []))
        if not body.get("has_more"):
            break
        payload["start_cursor"] = body["next_cursor"]

    return results

def extract(pages):
    records = []

    for page in pages:
        props = page.get("properties", {})

        # Date (tipo date)
        date_prop = props.get("Date", {})
        date_val = None
        if date_prop.get("type") == "date" and date_prop.get("date"):
            date_val = date_prop["date"].get("start")
        if not date_val:
            continue

        # Normalizza: prendi solo la parte YYYY-MM-DD
        date_str = date_val[:10]

        # Escludi attività in bici (nome contiene "Giro")
        name_prop = props.get("Name", props.get("title", {}))
        name_val = ""
        if name_prop.get("type") == "title":
            title_arr = name_prop.get("title", [])
            name_val = "".join(t.get("plain_text", "") for t in title_arr)
        if "Giro" in name_val or "Sci" in name_val:
            continue

        # Distance (number) (tipo number)
        dist_prop = props.get("Distance (number)", {})
        dist_val = None
        if dist_prop.get("type") == "number":
            dist_val = dist_prop.get("number")

        if dist_val is None or dist_val == 0:
            continue

        records.append({
            "date": date_str,
            "distance": round(dist_val, 2)
        })

    return records

if __name__ == "__main__":
    pages  = fetch_all_pages()
    data   = extract(pages)
    out    = os.path.join(os.path.dirname(__file__), "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Estratti e salvati {len(data)} record")
