"""
char_scraper.py
---------------
Fase 2 dari pipeline scrape data HSR Game8.

Membaca data link hasil Fase 1, mengunjungi setiap halaman detail karakter,
lalu Ngambil atribut lengkap (basic info, stats, build, materials).

Output (disimpan ke ../data/)
-----------------------------
  characters.json

Penggunaan
----------
  python char_scraper.py
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
    print(f"  [SAVED] {len(data)} entries -> {path}")


def parseBasicInfo(soup):
    # Ngambil Rarity, Path, dan Element dari tabel Basic Information
    info = {"rarity": None, "path": None, "element": None}

    target_th = soup.find("th", string=re.compile(r"Basic Information", re.IGNORECASE))
    if not target_th:
        return info

    table = target_th.find_parent("table")
    if not table:
        return info

    for row in table.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue

        label = th.get_text(strip=True).lower()
        value = td.get_text(separator=" ", strip=True)

        if "rarity" in label:
            # Ambil digit angka saja dari teks rating (e.g. "5-star")
            match = re.search(r"(\d+)", value)
            info["rarity"] = int(match.group(1)) if match else None
        elif "element" in label:
            info["element"] = value.strip()
        elif "path" in label:
            info["path"] = value.strip()

    return info


def parseBaseStats(soup):
    # Ngambil HP, ATK, DEF, dan SPD dari tabel tab Level 1 dan Level 80
    stat_map = {"hp": "hp", "atk": "atk", "def": "def", "spd": "spd"}
    result = {"level_1": {}, "level_80": {}}

    panels = soup.select("div.a-tabPanel")
    if len(panels) < 2:
        return result

    # Index 0 untuk Level 1, Index 1 untuk Level 80
    for panel_index, level_key in [(0, "level_1"), (1, "level_80")]:
        panel = panels[panel_index]
        for row in panel.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue

            label = th.get_text(separator=" ", strip=True).upper()
            label_value = td.find("div", class_="a-label")
            if not label_value:
                continue

            raw_num = label_value.get_text(strip=True).replace(",", "")
            try:
                num = int(raw_num)
            except ValueError:
                continue

            for key in stat_map:
                if key.upper() in label:
                    result[level_key][stat_map[key]] = num
                    break

    return result


def parseBestBuild(soup):
    # Ngambil rekomendasi Light Cone, Relic, dan Main Stat
    build = {
        "recommended_light_cones": [],
        "recommended_relics": [],
        "main_stats": {"body": [], "feet": [], "planar_sphere": [], "link_rope": []},
    }

    # Cari section best build
    build_header = soup.find(id="hl_2")
    if not build_header:
        return build

    tab_container = None
    for sibling in build_header.find_all_next():
        if sibling.name == "h2":
            break
        if sibling.get("class") and "a-tabContainer" in sibling.get("class"):
            tab_container = sibling
            break

    if not tab_container:
        return build

    panels = tab_container.select("div.a-tabPanel")
    if not panels:
        return build

    base_panel = panels[0]

    # Ambil Best Light Cone
    for a_tag in base_panel.find_all("a", href=True):
        img = a_tag.find("img")
        if img and "Light Cone" in img.get("alt", ""):
            name = a_tag.get_text(separator=" ", strip=True)
            if name:
                build["recommended_light_cones"].append(name)

    # Ambil opsi Alternative Light Cones di panel tab kedua
    if len(panels) > 1:
        alt_panel = panels[1]
        for a_tag in alt_panel.find_all("a", href=True):
            img = a_tag.find("img")
            if img and "Light Cone" in img.get("alt", ""):
                name = a_tag.get_text(separator=" ", strip=True)
                if name and name not in build["recommended_light_cones"]:
                    build["recommended_light_cones"].append(name)

    # Ambil rekomendasi Relic Sets (yang gambarny bukan Light Cone)
    for a_tag in base_panel.find_all("a", href=True):
        img = a_tag.find("img")
        if not img:
            continue
        alt = img.get("alt", "")
        if "Light Cone" in alt or "Star Rail" in alt:
            continue
        name = a_tag.get_text(separator=" ", strip=True)
        if name and name not in build["recommended_relics"]:
            build["recommended_relics"].append(name)

    # Ambil Main Stats dari kolom teks
    for td in base_panel.find_all("td"):
        raw_text = td.get_text(separator="\n", strip=True)

        if "Body" in raw_text and "Feet" in raw_text:
            for line in raw_text.splitlines():
                line = line.strip()
                if line.startswith("Body"):
                    stats = re.sub(r"Body\s*:", "", line, flags=re.IGNORECASE).strip()
                    build["main_stats"]["body"] = [s.strip() for s in stats.split(" or ") if s.strip()]
                elif line.startswith("Feet"):
                    stats = re.sub(r"Feet\s*:", "", line, flags=re.IGNORECASE).strip()
                    build["main_stats"]["feet"] = [s.strip() for s in stats.split(" or ") if s.strip()]
                elif "Sphere" in line:
                    stats = re.sub(r"Sphere\s*:", "", line, flags=re.IGNORECASE).strip()
                    build["main_stats"]["planar_sphere"] = [s.strip() for s in stats.split(" or ") if s.strip()]
                elif "Rope" in line:
                    stats = re.sub(r"Rope\s*:", "", line, flags=re.IGNORECASE).strip()
                    build["main_stats"]["link_rope"] = [s.strip() for s in stats.split(" or ") if s.strip()]

    return build


def parseMaterials(soup):
    # Ngambil Ascension dan Trace Materials dari section mats
    result = {"ascension": [], "traces": []}

    mat_header = soup.find(id="hl_6")
    if not mat_header:
        return result

    tables = []
    for sibling in mat_header.find_all_next():
        if sibling.name == "h2":
            break
        if sibling.name == "table":
            tables.append(sibling)

    keys = ["ascension", "traces"]

    # Ambil dua tabel pertama setelah header (Ascension dan Traces)
    for i, table in enumerate(tables[:2]):
        key = keys[i]
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            name_cell = tds[0]
            amount_cell = tds[1]

            name_link = name_cell.find("a")
            name = name_link.get_text(strip=True) if name_link else name_cell.get_text(strip=True)

            raw_amount = amount_cell.get_text(strip=True).replace(",", "")
            try:
                amount = int(raw_amount)
            except ValueError:
                continue

            if name:
                result[key].append({"name": name, "amount": amount})

    return result


def parseRecommendedStats(soup):
    # Ngambil target status build dan urutan prioritas sub stat
    result = {"main_stats": [], "sub_stats_priority": []}

    stat_header = soup.find(id="hm_5")
    if not stat_header:
        return result

    table = None
    for sibling in stat_header.find_all_next():
        if sibling.name == "h3":
            break
        if sibling.name == "table":
            table = sibling
            break

    if table:
        for row in table.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if not th or not td:
                continue
            stat_name = th.get_text(strip=True)
            stat_val = td.get_text(strip=True)
            if stat_name and stat_val:
                result["main_stats"].append({"stat": stat_name, "recommended_value": stat_val})

    # Mengambil urutan sub-stats berdasarkan jumlah bintang rating (★)
    build_header = soup.find(id="hl_2")
    if not build_header:
        return result

    for sibling in build_header.find_all_next():
        if sibling.name == "h2":
            break
        if sibling.name == "td":
            raw = sibling.get_text(separator="\n", strip=True)
            if "★" in raw and "CRIT" in raw:
                priority_rank = 1
                for line in raw.splitlines():
                    line = line.strip()
                    if "★" in line and line:
                        stat_name = line.split("★")[0].strip()
                        if stat_name:
                            result["sub_stats_priority"].append({
                                "stat": stat_name,
                                "priority_rank": priority_rank
                            })
                            priority_rank += 1
                break

    return result


def scrapeChar(char):
    # Load halaman char, return dictionary hasil parse
    name = char["name"]
    archive_id = char["archive_id"]
    url = char["url"]

    soup = fetch(url)
    if not soup:
        return None

    basic_info = parseBasicInfo(soup)
    base_stats = parseBaseStats(soup)
    best_build = parseBestBuild(soup)
    total_materials = parseMaterials(soup)
    recommended_stats = parseRecommendedStats(soup)

    return {
        "name": name,
        "archive_id": archive_id,
        "url": url,
        "basic_info": basic_info,
        "base_stats": base_stats,
        "best_build": best_build,
        "total_materials": total_materials,
        "recommended_stats": recommended_stats,
    }

def print2(text: str): 
    if(text[0] == '\n'):
        print("")
        print("    " + text[1:])
    else: print("    " + text)

def phase2():
    print2("[Phase 2] Mulai scraping detail karakter HSR...")

    with open("../data/character_links.json", "r", encoding="utf-8") as f:
        charJSON = json.load(f)

    all_chars = []
    for i, char in enumerate(charJSON):
        print2((f"\n[FETCH {i+1}/{len(charJSON)}] Fetching {char['name']}'s page"))
        result = scrapeChar(char)
        if result:
            all_chars.append(result)

    saveJSON(all_chars, "characters.json")
    print("\n[Phase 2] Selesai.")

phase2()