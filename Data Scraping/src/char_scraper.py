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

def saveJSON(data: list, filename: str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)
    print(f"  [SAVED] {len(data)} entries -> {path}")

def scrapeCharLink(soup: BeautifulSoup):
    # Tiap char ada <img> alt="Star Rail - <CharacterName>"
    # Tinggal cari itu, baru ke parent <a> dapat kita url + namanya di textfield
    results: list[dict] = []
    seen: set[str] = set()
    char_imgs = soup.find_all(
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

def print2(text: str):
    print("\t" + text)

def scrapeChar():
    print2("[JSON] Read character_links.json")