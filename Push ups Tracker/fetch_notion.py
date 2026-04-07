import os
import json
import requests
from datetime import datetime

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID  = "29e42ff37a058078a70bdc2f9d00efae"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def fetch_all_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    results = []
    payload = {"sorts": [{"property": "date", "direction": "ascending"}]}

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
    labels = []
    total_pushups = []

    for page in pages:
        props = page.get("properties", {})

        # Data (proprietà "date", tipo date)
        date_prop = props.get("date", {})
        date_val = None
        if date_prop.get("type") == "date" and date_prop.get("date"):
            date_val = date_prop["date"].get("start")
        if not date_val:
            continue
        label = datetime.fromisoformat(date_val).strftime("%-d %b %Y")

        # Total push-ups (tipo formula -> numero)
        pushup_prop = props.get("Total push-ups", {})
        pushup_val = None
        if pushup_prop.get("type") == "formula":
            pushup_val = pushup_prop.get("formula", {}).get("number")

        if not pushup_val:  # ignora None e 0
            continue

        labels.append(label)
        total_pushups.append(pushup_val)

    return {"labels": labels, "total_pushups": total_pushups}

if __name__ == "__main__":
    pages = fetch_all_pages()
    data  = extract(pages)
    out   = os.path.join(os.path.dirname(__file__), "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Estratti e salvati {len(data['labels'])} record")
