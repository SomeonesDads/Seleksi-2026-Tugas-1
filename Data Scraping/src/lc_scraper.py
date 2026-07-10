"""
Kerangka:
{

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

def scrapeLC(lc):
    # Load halaman lc, return dictionary hasil parse
    name = lc["name"]
    archive_id = lc["archive_id"]
    url = lc["url"]

    return {

    }

def print2(text: str): 
    if(text[0] == '\n'):
        print("")
        print("    " + text[1:])
    else: print("    " + text)

def scrapeLCs():
    with open("../data/light_cone_links.json", "r", encoding="utf-8") as f:
        lcJSON = json.load(f)

    all_LCs = []
    for i, lc in enumerate(lcJSON):
        print2((f"[FETCH {i+1}/{len(lcJSON)}] Fetching {lc['name']}'s page..."))
        result = scrapeLC(lc)
        if result:
            all_LCs.append(result)

    saveJSON(all_LCs, "light_cone.json")
