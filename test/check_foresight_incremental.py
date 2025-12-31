import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from crawler.database.db_sqlite import Database
from crawler.scrapers.foresight_article import ForesightDepthScraper

def check_incremental():
    db = Database()
    scraper = ForesightDepthScraper()
    
    print(f"Scraper Site Name: '{scraper.site_name}'")
    
    # Manually load last news
    print("Loading last news...")
    scraper.load_last_news(db)
    
    print(f"Last News URL: {scraper.last_news_url}")
    print(f"Existing URLs count: {len(scraper.existing_urls)}")
    
    # Check specific URL from logs
    test_url = "https://foresightnews.pro/article/detail/93356"
    print(f"Checking URL: {test_url}")
    
    if test_url in scraper.existing_urls:
        print("✅ URL Found in existing_urls. Incremental check SHOULD work.")
    else:
        print("❌ URL NOT Found in existing_urls. Incremental check will FAIL.")
        
    # Check what IS in existing urls (sample)
    if scraper.existing_urls:
        print("Sample existing URLs:")
        for url in list(scraper.existing_urls)[:3]:
            print(f"  - {url}")

if __name__ == "__main__":
    check_incremental()
