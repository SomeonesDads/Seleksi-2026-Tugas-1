"""
Phase 2: Dari masing masing file links, kita mau scraping data satu-satu
Kita save ke data dalam bentuk json
- characters.json
- light_cone.json
- relic.json
- 
"""

import char_scraper, lc_scraper, relic_scraper, misc_scraper, test_missing_lcs


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept-Language": "en-US,en;q=0.9",
}

def phase2():
    print("\n[STEP 1/4] Visiting character links...")
    char_scraper.scrapeChars()
    print("\n[STEP 2/4] Visiting light cone links...")
    lc_scraper.scrapeLCs()
    print("\n[STEP 3/4] Visiting relic links...")
    relic_scraper.scrapeRelics()
    print("\n[STEP 4/4] Visiting material hub...")
    misc_scraper.scrapeMiscs()
    test_missing_lcs.fix()
    

    

    print("\n[DONE] All link queues saved to the data/ folder.")

