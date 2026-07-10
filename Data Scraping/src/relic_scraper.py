"""
Kerangka:
{
    "name": "Poet of Mourning Collapse",
    "archive_id": "492444",
    "url": "https://game8.co/games/Honkai-Star-Rail/archives/492444"
    "type": "relic" | "planar" (Kalo planar cuma ada 2_piece)
    "set_effects": {
        2_piece: "Increases Quantum DMG by 10%."
        4_piece: "Decreases the wearer's SPD by 8%. Before entering battle, if the wearer's SPD is less than 110/95, increases the wearer's CRIT Rate by 20%/32%. This effect also applies to the wearer's memosprite."
    }
}
"""

import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY = 2.0
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def fetch(url):
    # Mengambil dokumen HTML dengan jeda request agar sopan
    time.sleep(REQUEST_DELAY)
    # print(f"  [FETCH] {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"  [ERROR] HTTP {response.status_code}")
            return None
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print(f"  [EXCEPTION] {exc}")
        return None

def saveJSON(data, filename):
    # Menyimpan list data ke file JSON tujuan
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)
    print(f"    \n[SAVED] {len(data)} entries -> {path}\n")

def scrapeRelic(relic):
    # Load halaman relic, return dictionary hasil parse
    toKey = {"Cavern Relic": "relic", "Planar Ornament": "planar"}
    name = relic["name"]
    archive_id = relic["archive_id"]
    url = relic["url"]
    ans =  {
        "name": name,
        "archive_id": archive_id,
        "url": url,
        "type": None,
        "set_effects": None,
    }

    soup = fetch(url)
    if not soup:
        return ans

    target_h3 = soup.find("h3", string=re.compile(r"Set Effects", re.IGNORECASE))
    if not target_h3:
        return ans

    table = target_h3.find_next_sibling("table")
    if not table:
        return ans
    
    trs = table.find_all("tr")
    if len(trs) < 3: return ans

    def getEffect(trs, index):
        return trs[index].find("td").get_text(strip=True)

    ans["type"] = toKey[trs[0].get_text(strip=True)]
    if(ans["type"] == "relic"):
        set_effects = {"2pc_effect": getEffect(trs, 2), "4pc_effect": getEffect(trs, 3)}

    elif(ans["type"] == "planar"):
        set_effects = {"2pc_effect": getEffect(trs, 2)}

    ans["set_effects"] = set_effects
    return ans

def print2(text: str): 
    if(text[0] == '\n'):
        print("")
        print("    " + text[1:])
    else: print("    " + text)

def scrapeRelics():
    with open("../data/relic_links.json", "r", encoding="utf-8") as f:
        relicJSON = json.load(f)

    all_relics = []
    for i, relic in enumerate(relicJSON):
        print2((f"[FETCH {i+1}/{len(relicJSON)}] Fetching {relic['name']}'s page..."))
        result = scrapeRelic(relic)
        if result:
            all_relics.append(result)

    saveJSON(all_relics, "relic.json")