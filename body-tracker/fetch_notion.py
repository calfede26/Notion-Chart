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

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
PAGE_ID = "e668113e66b24746968d1c87041ceadd"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

def fetch_children(block_id):
    """Restituisce i figli diretti di un blocco/pagina."""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json().get("results", [])

def fetch_all_blocks(block_id):
    """Fetch ricorsivo di tutti i blocchi."""
    all_blocks = []
    children = fetch_children(block_id)

    for block in children:
        all_blocks.append(block)
        if block.get("has_children"):
            all_blocks.extend(fetch_all_blocks(block["id"]))

    return all_blocks

def extract_text_from_block(block):
    """
    Estrae tutto il testo leggibile dal blocco:
    - rich_text del blocco
    - children ricorsivi, se presenti
    """
    parts = []

    btype = block.get("type", "")
    inner = block.get(btype, {})

    rich = inner.get("rich_text", inner.get("text", []))
    for rt in rich:
        parts.append(rt.get("plain_text", ""))

    if block.get("has_children"):
        for child in fetch_children(block["id"]):
            parts.append(extract_text_from_block(child))

    return "".join(parts)

def parse_weeks(blocks):
    weeks = []

    week_re  = re.compile(r"Week\s+(\d+)\s*\(([^)]+)\)")
    km_re    = re.compile(r"([\d]+(?:\.[\d]+)?)\s*km")
    sleep_re = re.compile(r"(\d+)\s*pt")
    push_re  = re.compile(r"(\d+)\s*total")

    for block in blocks:
        if block.get("type") != "callout":
            continue

        text = extract_text_from_block(block)

        print("DEBUG callout letto:", repr(text))

        wm = week_re.search(text)
        km_m = km_re.search(text)
        sleep_m = sleep_re.search(text)
        push_m = push_re.search(text)

        if not (wm and km_m and sleep_m and push_m):
            continue

        weeks.append({
            "label": f"S{wm.group(1)}\n{wm.group(2)}",
            "week_num": int(wm.group(1)),
            "km": float(km_m.group(1)),
            "sleep_score": int(sleep_m.group(1)),
            "pushups": int(push_m.group(1)),
        })

    return weeks

def main():
    blocks = fetch_all_blocks(PAGE_ID)
    print(f"DEBUG: trovati {len(blocks)} blocchi totali")

    weeks = parse_weeks(blocks)

    if not weeks:
        print("Nessuna settimana trovata — controlla i permessi del token o il formato dei callout.")
        return

    weeks.sort(key=lambda w: w["week_num"])
    output = {
        "updated": datetime.datetime.utcnow().isoformat() + "Z",
        "weeks": weeks,
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "data.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Scritto {output_path} con {len(weeks)} settimane.")

if __name__ == "__main__":
    main()
