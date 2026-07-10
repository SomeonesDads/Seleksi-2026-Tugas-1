import link_scraper
import data_scraper
import cleaner

print("Mulai Data Scraping Pipeline...")
print("=" * 55)
print(" Phase 1: Scraping links from hub ")
print("=" * 55)
link_scraper.phase1()
print("=" * 55)
print(" Phase 2: Scraping data from collected links ")
print("=" * 55)
data_scraper.phase2()
print("=" * 55)
print(" Phase 3: Cleaning JSON ")
print("=" * 55)
cleaner.phase3()
print("Data Scraping don")
