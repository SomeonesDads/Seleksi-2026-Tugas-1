"""
Step 2: Dari masing masing file links, kita mau scraping data satu-satu
- Characters    : https://game8.co/games/Honkai-Star-Rail
                  Identified by img alt="Star Rail - <Name>" in the
                  character grid section of the main wiki page.
- Light Cones   : https://game8.co/games/Honkai-Star-Rail/archives/406599
                  Structured table with Cone_cell / Rarity_cell / Path_cell.
- Relic Sets    : https://game8.co/games/Honkai-Star-Rail
                  Listed in the Relic Sets section (id="hl_10") of the
                  main wiki page.

Kita save ke data dalam bentuk json
- characters.json
- light_cone.json
- relic.json

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
import char_scraper, lc_scraper, relic_scraper
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept-Language": "en-US,en;q=0.9",
}

def phase2():
    print("=" * 55)
    print(" Phase 2: Scraping data from collected links ")
    print("=" * 55)
    print("\n[STEP 1/3] Visiting character links...")
    char_scraper.scrapeChar()
    print("\n[STEP 2/3] Visiting light cone links...")
    lc_scraper.scrapeLC()
    print("\n[STEP 3/3] Visiting relic links...")
    relic_scraper.scrapeRelic()
    print("\n[DONE] All link queues saved to the data/ folder.")

