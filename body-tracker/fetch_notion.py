"""
fetch_notion.py
Legge la pagina Body Tracker da Notion e genera body-tracker/data.json con i dati delle settimane.
Dipendenze: requests (pip install requests)
"""
import re
import json
import os
import datetime
import requests

NOTION_TOKEN   = os.environ["NOTION_TOKEN"]
PAGE_ID        = "e668113e66b24746968d1c87041ceadd"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def fetch_blocks(page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json().get("results", [])

def block_plain_text(block):
    """Estrae tutto il testo grezzo da un blocco (callout, paragraph, heading, ecc.)"""
    parts = []
    rich = []
    btype = block.get("type", "")
    inner = block.get(btype, {})
    # Il rich_text può essere dentro "rich_text" o "text"
    rich = inner.get("rich_text", inner.get("text", []))
    for rt in rich:
        parts.append(rt.get("plain_text", ""))
    return "".join(parts)

def parse_weeks(blocks):
    weeks = []
    # Pattern per estrarre i dati da ogni callout
    week_re  = re.compile(r"Week\s+(\d+)\s*\(([^)]+)\)")
    km_re    = re.compile(r"([\d]+(?:\.[\d]+)?)\s*km")
    leep_re = re.compile(r"(\d+)\s*pt")
    push_re  = re.compile(r"(\d+)\s*total")
    for block in blocks:
        if block.get("type") != "callout":
            continue
        text = block_plain_text(block)
        wm = week_re.search(text)
        if not wm:
            continue
        km_m    = km_re.search(text)
        sleep_m = sleep_re.search(text)
        push_m  = push_re.search(text)
        if not (km_m and sleep_m and push_m):
            continue
        weeks.append({
            "label":       f"S{wm.group(1)}\n{wm.group(2)}",
            "week_num":    int(wm.group(1)),
            "km":          float(km_m.group(1)),
            "sleep_score": int(sleep_m.group(1)),
            "pushups":     int(push_m.group(1)),
        })
    return weeks

def main():
    blocks = fetch_blocks(PAGE_ID)
    weeks  = parse_weeks(blocks)
    if not weeks:
        print("Nessuna settimana trovata — controlla il formato dei blocchi.")
        return
    weeks.sort(key=lambda w: w["week_num"])
    output = {
        "updated": datetime.datetime.utcnow().isoformat() + "Z",
        "weeks":   weeks,
    }
    import os  
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
    OUTPUT_PATH = os.path.join(BASE_DIR, "body-tracker", "data.json")  
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Scritto body-tracker/data.json con {len(weeks)} settimane.")

if __name__ == "__main__":
    main()
