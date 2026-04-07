"""
Habit Tracker/fetch_tracker.py
Legge il database Tracker da Notion e genera Habit-Tracker/data.json
con la percentuale di abitudini completate per ogni giorno.
Dipendenze: requests
"""
import json, os, datetime, requests

NOTION_TOKEN  = os.environ["NOTION_TOKEN"]
DATABASE_ID   = "e08f5234-1acb-481d-a15c-8de806d5dc7e"
HABITS        = ["Run", "Workout", "Stretch", "Read", "Drink", "Learn / fix / create", "No gooning"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def fetch_all_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    results, cursor = [], None
    while True:
        body = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        res = requests.post(url, headers=HEADERS, json=body)
        res.raise_for_status()
        data = res.json()
        results += data["results"]
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    return results

def parse_days(pages):
    days = []
    for page in pages:
        props = page["properties"]
        date_prop = props.get("Date", {}).get("date")
        if not date_prop or not date_prop.get("start"):
            continue
        date_str = date_prop["start"]
        checked = sum(
            1 for h in HABITS
            if props.get(h, {}).get("checkbox", False)
        )
        pct = round(checked / len(HABITS) * 100)
        days.append({"date": date_str, "pct": pct, "checked": checked, "total": len(HABITS)})
    days.sort(key=lambda d: d["date"])
    return days

def main():
    pages = fetch_all_pages()
    days  = parse_days(pages)
    os.makedirs("tracker", exist_ok=True)
    output = {
        "updated": datetime.datetime.utcnow().isoformat() + "Z",
        "habits": HABITS,
        "days": days,
    }
    with open("Habit Tracker/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Estratti e salvati: {len(days)} giorni.")

if __name__ == "__main__":
    main()
