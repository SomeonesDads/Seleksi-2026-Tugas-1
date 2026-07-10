"""
Kerangka:
{
    "name": "Auspice Sliver",
    "rarity": 2 | 3 | 4 | 5
    "type": trace_mat | ascension_mat | currency
}
"""

import json
import os
import requests
import time
from bs4 import BeautifulSoup

URL = "https://game8.co/games/Honkai-Star-Rail/archives/407120"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY = 2.0
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Border items yang jadi penanda batas rarity (dibaca baris per baris, kiri ke kanan)
# Semua item sebelum RARITY_3_START = rarity 4
# Semua item antara RARITY_3_START dan RARITY_2_START = rarity 3
# Semua item dari RARITY_2_START ke bawah = rarity 2
RARITY_3_START = "Sprout of Life"
RARITY_2_START = "Seed of Abundance"

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


def scrapeMisc(name, rarity, mat_type):
    return {
        "name": name,
        "rarity": rarity,
        "type": mat_type
    }

def print2(text: str): 
    if(text[0] == '\n'):
        print("")
        print("    " + text[1:])
    else: print("    " + text)

def scrapeMiscs():
    print2((f"[FETCH 1/1] Fetching material's page..."))
    soup = fetch(URL)
    all_mats = []
    all_mats.append(scrapeMisc("Credit", "3", "currency"))

    asc_header = soup.find(id="hm_2")
    trace_header = soup.find(id="hm_3")
    next_h2 = soup.find(id="hl_2")

    table = None
    node = asc_header.find_next_sibling()
    while node and node != trace_header:
        if node.name == "table":
            table = node
            break
        node = node.find_next_sibling()

    if table:
        ordered_names = []
        seen = set()
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue
            for cell in cells:
                a = cell.find("a")
                if not a or not a.find("img"):
                    continue
                name = a.get_text(strip=True)
                if name and name not in seen:
                    seen.add(name)
                    ordered_names.append(name)

        current_rarity = 4
        for name in ordered_names:
            if name == RARITY_3_START:
                current_rarity = 3
            elif name == RARITY_2_START:
                current_rarity = 2
            all_mats.append(scrapeMisc(name, current_rarity, "ascension_mat"))

    seen = set()
    node = trace_header.find_next_sibling()
    while node and node != next_h2:
        if node.name == "table":
            for a in node.find_all("a"):
                if not a.find("img"):
                    continue
                name = a.get_text(strip=True)
                if not name or name in seen:
                    continue
                seen.add(name)
                rarity = 5 if name.lower() == "tracks of destiny" else 4
                all_mats.append(scrapeMisc(name, rarity, "trace_mat"))
        node = node.find_next_sibling()

    saveJSON(all_mats, "materials.json")