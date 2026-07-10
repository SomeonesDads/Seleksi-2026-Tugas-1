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
        if not th:
            continue
        td = th.find_next_sibling("td")
        if not td:
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


def normalizeSubStat(text):
    if(text == "Effect Hit Rate %" or text == "Effect Hit Rate%"): return "EHR"
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

def normalizeStatName(stat):
    # Menormalkan nama stat (e.g. EHR dan Effect RES)
    stat_clean = stat.strip()
    if stat_clean.lower().startswith("effect hit"):
        return "EHR"
    if stat_clean.lower().startswith("effect res"):
        return "Effect RES"
    return stat_clean


def splitAndNormalize(stat_str):
    # Memisahkan stat yang digabung dengan "/"
    parts = stat_str.split("/")
    result = []
    for p in parts:
        normalized = normalizeStatName(p)
        if normalized:
            result.append(normalized)
    return result


    # Ambil Main Stats dari kolom teks
    for td in base_panel.find_all("td"):
        raw_text = td.get_text(separator=" ", strip=True)

        if "Body" in raw_text and "Feet" in raw_text:
            body_m = re.search(r"Body\s*:\s*(.*?)(?:Feet|Sphere|Rope|$)", raw_text, re.IGNORECASE)
            feet_m = re.search(r"Feet\s*:\s*(.*?)(?:Sphere|Rope|$)", raw_text, re.IGNORECASE)
            sphere_m = re.search(r"Sphere\s*:\s*(.*?)(?:Rope|$)", raw_text, re.IGNORECASE)
            rope_m = re.search(r"Rope\s*:\s*(.*?)(?:$)", raw_text, re.IGNORECASE)
            
            if body_m:
                stats = []
                for s in body_m.group(1).split(" or "):
                    stats.extend(splitAndNormalize(s))
                build["main_stats"]["body"] = stats
            if feet_m:
                stats = []
                for s in feet_m.group(1).split(" or "):
                    stats.extend(splitAndNormalize(s))
                build["main_stats"]["feet"] = stats
            if sphere_m:
                stats = []
                for s in sphere_m.group(1).split(" or "):
                    stats.extend(splitAndNormalize(s))
                build["main_stats"]["planar_sphere"] = stats
            if rope_m:
                stats = []
                for s in rope_m.group(1).split(" or "):
                    stats.extend(splitAndNormalize(s))
                build["main_stats"]["link_rope"] = stats

    return build


def parseMaterials(soup):
    # Ngambil Ascension dan Trace Materials dari section mats
    result = {"ascension": [], "traces": []}

    mat_th = soup.find(lambda tag: tag.name in ["h2", "h3"] and "Materials" in tag.text)
    if not mat_th:
        return result

    tables = []
    for sibling in mat_th.find_all_next():
        if sibling.name == "h2":
            break
        if sibling.name == "table":
            tables.append(sibling)

    ascension_table = None
    traces_table = None

    for tbl in tables:
        th_texts = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
        header = " ".join(th_texts)
        if "ascension" in header and "total" in header:
            if not ascension_table: ascension_table = tbl
        if "trace" in header and "total" in header:
            if not traces_table: traces_table = tbl

    def parse_table(table):
        if not table: return []
        res = []
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            name_link = tds[0].find("a")
            name = name_link.get_text(strip=True) if name_link else tds[0].get_text(strip=True)
            raw_amt = tds[1].get_text(strip=True).replace(",", "")
            try:
                amt = int(raw_amt)
                if name: res.append({"name": name, "amount": amt})
            except ValueError:
                pass
        return res

    result["ascension"] = parse_table(ascension_table)
    result["traces"] = parse_table(traces_table)

    return result


def parseRecommendedStats(soup):
    # Ngambil urutan prioritas sub stat
    result = {"sub_stats_priority": []}

    # Mengambil urutan sub-stats berdasarkan jumlah bintang rating (★)
    build_header = soup.find(id="hl_2")
    if not build_header:
        return result

    for sibling in build_header.find_all_next():
        if sibling.name == "h2":
            break
        if sibling.name == "td":
            raw = sibling.get_text(separator="\n", strip=True)
            if "★" in raw:
                priority_rank = 1
                for line in raw.splitlines():
                    line = line.strip()
                    if "★" in line and line:
                        stat_name = line.split("★")[0].strip()
                        if stat_name:
                            split_stats = splitAndNormalize(stat_name)
                            for s in split_stats:
                                result["sub_stats_priority"].append({
                                    "stat": s,
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