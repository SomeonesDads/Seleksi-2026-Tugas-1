"""
Kerangka:
{
    "name": "In the Name of the World",
    "archive_id": "408535",
    "url": "https://game8.co/games/Honkai-Star-Rail/archives/408535",

    "basic_info": {
        "rarity": 5,
        "path": "The Nihility"
    },

    "base_stats": {
        "level_1": {
            "hp": 48,
            "atk": 26,
            "def": 21
        },
        "level_80": {
            "hp": 1058,
            "atk": 582,
            "def": 463
        }
    },

    "passive_skill": {
        "name": "Inheritor",
        "description": "Increases the wearer's DMG to debuffed enemies by 24%/28%/32%/36%/40%. When the wearer uses their Skill, the Effect Hit Rate for this attack increases by 18%/21%/24%/27%/30%, and ATK increases by 24%/28%/32%/36%/40%."
    },

    "total_materials": {
        "ascension": [
            {
                "name": "Silvermane Badge",
                "amount": 20
            },
            {
                "name": "Obsidian of Dread",
                "amount": 4
            },
            {
                "name": "Obsidian of Desolation",
                "amount": 12
            },
            {
                "name": "Silvermane Insignia",
                "amount": 20
            },
            {
                "name": "Obsidian of Obsession",
                "amount": 15
            },
            {
                "name": "Silvermane Medal",
                "amount": 14
            },
            {
                "name": "Credit",
                "amount": 385000
            }
        ]
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

def parseBasicInfo(soup):
    # Ngambil Rarity, Path tabel Basic Information
    info = {"rarity": None, "path": None}

    target_h3 = soup.find("h3", string=re.compile(r"Effects and Overview", re.IGNORECASE))
    if not target_h3:
        return info

    table = target_h3.find_next_sibling("table")
    if not table:
        return info
    
    for row in table.find_all("tr"):
        th = row.find("th")
        if not th:
            continue
        td = th.find_next_sibling("td")
        if not td:
            continue

        label = th.get_text(strip=True).lower()
        value = td.get_text(separator=" ", strip=True)

        if "rarity" in label:
            if "★" in value:
                info["rarity"] = len(value)
        elif "path" in label:
            info["path"] = value.strip()

    return info


def parseBaseStats(soup):
    # Ngambil HP, ATK, DEF dari tabel tab Level 1 dan Level 80
    result = {"level_1": {}, "level_80": {}}

    target_h3 = soup.find("h3", string=re.compile(r"Stats", re.IGNORECASE))
    if not target_h3:
        return result

    table = target_h3.find_next_sibling("table")
    
    for row in table.find_all("tr"):
        th = row.find("th")
        if not th:
            continue

        label = th.get_text(strip=True).lower()
    
        if(label == '1'):
            tds = row.find_all("td")

            if len(tds) >= 3:
                result["level_1"] = {
                    "hp": int(tds[0].get_text(strip=True)),
                    "atk": int(tds[1].get_text(strip=True)),
                    "def": int(tds[2].get_text(strip=True)),
                }
            
        if(label == '80'):
            tds = row.find_all("td")

            if len(tds) >= 3:
                result["level_80"] = {
                    "hp": int(tds[0].get_text(strip=True)),
                    "atk": int(tds[1].get_text(strip=True)),
                    "def": int(tds[2].get_text(strip=True)),
                }

    return result

def parseMaterials(soup):
    # Ngambil Ascension dan Trace Materials dari section mats
    result = {"ascension": []}
    target_h3 = soup.find("h3", string=re.compile(r"Total Ascension Materials", re.IGNORECASE))
    if not target_h3:
        return result

    table = target_h3.find_next_sibling("table")
    if not table:
        return result
    
    for row in table.find_all("tr"):
        tds = row.find_all("td")
        if len(tds) >= 2:
            if(tds[0].get_text(strip=True) != "Ascension Material"):
                result["ascension"].append(
                    {
                        "name": tds[0].get_text(strip=True),
                        "amount": int(tds[1].get_text(strip=True))
                    })
    return result

def parsePassiveSkill(soup):
    result = {"name": None, "description": None}

    target_h3 = soup.find("h3", string=re.compile(r"Effects and Overview", re.IGNORECASE))
    if not target_h3:
        return result

    table = target_h3.find_next_sibling("table")
    if not table:
        return result
    
    for row in table.find_all("tr"):
        th = row.find("th")
        if not th:
            continue
        td = th.find_next_sibling("td")
        if not td:
            continue

        label = th.get_text(strip=True).lower()

        if "ability" in label:
            name = td.find("b").get_text(strip=True)
            description = td.get_text(separator=" ", strip=True)
            description = description.removeprefix(name).strip().replace(" .", ".").replace(" ,", ",") # Saia Pintar!
            result["name"] = name
            result["description"] = description

    return result



def saveJSON(data, filename):
    # Menyimpan list data ke file JSON tujuan
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)
    print(f"    \n[SAVED] {len(data)} entries -> {path}\n")

def scrapeRelic(relic):
    # Load halaman relic, return dictionary hasil parse
    name = relic["name"]
    archive_id = relic["archive_id"]
    url = relic["url"]

    soup = fetch(url)
    if not soup:
        return None

    basic_info = parseBasicInfo(soup)
    base_stats = parseBaseStats(soup)
    passive_skill = parsePassiveSkill(soup)
    total_materials = parseMaterials(soup)

    return {
        "name": name,
        "archive_id": archive_id,
        "url": url,
        "basic_info": basic_info,
        "base_stats": base_stats,
        "passive_skill": passive_skill,
        "total_materials": total_materials,
    }

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