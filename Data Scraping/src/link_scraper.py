"""
Step 1: Kita ngambil semua link-link yang punya data data Char, Light Cone, Relic.
- Characters    : https://game8.co/games/Honkai-Star-Rail
                  Identified by img alt="Star Rail - <Name>" in the
                  character grid section of the main wiki page.
- Light Cones   : https://game8.co/games/Honkai-Star-Rail/archives/406599
                  Structured table with Cone_cell / Rarity_cell / Path_cell.
- Relic Sets    : https://game8.co/games/Honkai-Star-Rail
                  Listed in the Relic Sets section (id="hl_10") of the
                  main wiki page.

Kita save ke data dalam bentuk json
- character_links.json
- light_cone_links.json
- relic_links.json

Kerangka:
{   
    "name": "Acheron", 
    "archive_id": "436053",
    "url": "https://game8.co/games/Honkai-Star-Rail/archives/436053" 
}
"""

import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup


MAIN_HSR_PAGE   = "https://game8.co/games/Honkai-Star-Rail"
HUB_LIGHT_CONES = "https://game8.co/games/Honkai-Star-Rail/archives/406599"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_DELAY = 2.0
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def fetch(url: str):
    time.sleep(REQUEST_DELAY)
    print(f"[FETCH] {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"  [ERROR] HTTP {response.status_code}")
            return None
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print(f"  [EXCEPTION] {exc}")
        return None


def extractArchive(href: str):
    match = re.search(r"/archives/(\d+)", href)
    return match.group(1) if match else None # None buat yg aneh kya boothill


def saveJSON(data: list, filename: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)
    print(f"  [SAVED] {len(data)} entries -> {path}")


def scrapeCharLink(soup: BeautifulSoup):
    # Tiap char ada <img> alt="Star Rail - <CharacterName>"
    # Tinggal cari itu, baru ke parent <a> dapat kita url + namanya di textfield
    # Perketat lagi, hanya ngambil img dari children char table, ditandai children yang memiliki text list of all characters

    # EXCLUDEARCHIVE = [608550, 485994, 408464, 408462, 408463, 408461, 408460, 408459, 408458, 530842, 608552, 608551, 530841] # Masuk rupanya beberapa LC

    results: list[dict] = []
    seen: set[str] = set()

    marker = soup.find("th", string=re.compile(r"List of All Characters", re.IGNORECASE))
    if not marker:
        print("  [ERROR] Could not find 'List of All Characters' table header.")
        return []
    
    char_table = marker.find_parent("table")
    if not char_table:
        print("  [ERROR] Parent table for characters not found.")
        return []
    
    char_imgs = char_table.find_all(
        "img",
        alt=re.compile(r"^Star Rail - .+")
    )

    for img in char_imgs:
        parent_a = img.find_parent("a")
        if not parent_a: continue
        
        href = parent_a.get("href", "")
        if not href or "archives" not in href and "Best-Builds" not in href: continue
        
        if href.startswith("http"):
            url = href
        else:
            url = "https://game8.co" + href
        if url in seen:
            continue
        
        seen.add(url)
        raw_alt = img.get("alt", "")
        name = raw_alt.replace("Star Rail - ", "").strip()
        if not name:
            name = parent_a.get_text(strip=True)
        archive_id = extractArchive(href)   

        results.append({
            "name"       : name,
            "archive_id" : archive_id,
            "url"        : url,
        })

    return results


def scrapeLCLink(soup: BeautifulSoup):
    # Hub page punya tabel class "a-table", isiny data Cone_cell, Rarity_cell, dan Path_cell
    # Kita loop setiap <tr> yang memiliki data Cone_cell untuk ambil nama + url-nya
    results: list[dict] = []
    seen: set[str] = set()
    for row in soup.find_all("tr"):
        cone_cell   = row.find("td", class_="Cone_cell")
        if not cone_cell: continue  

        cone_link = cone_cell.find("a", href=re.compile(r"/archives/\d+"))
        if not cone_link: continue

        href = cone_link.get("href", "")
        archive_id = extractArchive(href)
        if not archive_id or archive_id in seen: continue

        name = cone_link.get_text(separator=" ", strip=True)  # get_text(separator=" ") karena ada <img> sebelum namany

        seen.add(archive_id)
        results.append({
            "name"       : name,
            "archive_id" : archive_id,
            "url"        : f"https://game8.co/games/Honkai-Star-Rail/archives/{archive_id}",
        })
    return results


def scrapeRelicLink(soup: BeautifulSoup):
    # Nyari section id="hl_10", ambil seluruh tag <a> setelahnya sampai ketemu h2 berikutnya
    # Kalau id tidak ditemukan, ada skema fallback scan seluruh halaman berdasarkan regex archives
    results: list[dict] = []
    seen: set[str] = set()

    
    EXCLUDED_ID = "406599",   # Light Cone hub, muncul
    

    # Cari section header Relic Sets
    relic_header = soup.find(id="hl_10")
    if relic_header is None:
        print("  [WARN] Could not find relic section by id; falling back to full-page scan.")
        all_links = soup.find_all("a", href=re.compile(r"/games/Honkai-Star-Rail/archives/\d+"))
    else:
        section_links = []
        for sibling in relic_header.find_all_next():
            if sibling.name == "h2" and sibling != relic_header:
                break
            if sibling.name == "a":
                section_links.append(sibling)
        all_links = section_links

    for tag in all_links:
        href = tag.get("href", "")
        if not href or not re.search(r"/archives/\d+", href):
            continue

        archive_id = extractArchive(href)
        name = tag.get_text(separator=" ", strip=True)

        if not archive_id or not name:
            continue
        if archive_id in seen or archive_id == EXCLUDED_ID:
            continue
        if len(name) < 2:
            continue

        # Skip link navigasi luar/bukan item relic asli berdasarkan kata kunci
        name_lower = name.lower()
        skip_keywords = {
            "tier list", "how to", "all characters", "all light cones",
            "guide", "wiki home", "list of all", "upcoming",
        }
        if any(kw in name_lower for kw in skip_keywords):
            continue

        seen.add(archive_id)
        full_url = (
            href if href.startswith("http")
            else f"https://game8.co{href}"
        )
        results.append({
            "name"       : name,
            "archive_id" : archive_id,
            "url"        : full_url,
        })

    return results


def phase1():
    print("\n[FETCH 1/2] Fetching main HSR wiki page...")
    main_soup = fetch(MAIN_HSR_PAGE)
    if main_soup is None:
        print("[ABORT] Could not fetch main page. Exiting.")
        return
    print("\n[FETCH 2/2] Fetching Light Cone hub page...")
    lc_soup = fetch(HUB_LIGHT_CONES)
    if lc_soup is None:
        print("[ABORT] Could not fetch Light Cone hub. Exiting.")
        return

    print("\n[STEP 1/3] Extracting character links...")
    characters = scrapeCharLink(main_soup)
    print(f"  -> Found {len(characters)} characters")
    saveJSON(characters, "character_links.json")

    print("\n[STEP 2/3] Extracting light cone links...")
    light_cones = scrapeLCLink(lc_soup)
    print(f"  -> Found {len(light_cones)} light cones")
    saveJSON(light_cones, "light_cone_links.json")

    print("\n[STEP 3/3] Extracting relic set links...")
    relics = scrapeRelicLink(main_soup)
    print(f"  -> Found {len(relics)} relic sets")
    saveJSON(relics, "relic_links.json")

    print("\n[DONE] All link queues saved to the data/ folder.")