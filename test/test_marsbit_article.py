
import asyncio
import sys
import os

# Create a minimal mock DB to verify type is passed correctly
class MockDB:
    def get_latest_news(self, site_name):
        return None
    def insert_news(self, news_item):
        print(f"✅ DB Insert called for: {news_item.get('title')[:20]}... | Type: {news_item.get('type')}")
        return 1

async def test_scraper():
    # Setup path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    
    from crawler.scrapers.marsbit_article import MarsBitArticleScraper
    
    scraper = MarsBitArticleScraper()
    # Mock DB for incremental check (although we return None above)
    scraper.load_last_news(MockDB()) 
    
    try:
        await scraper.init_browser(headless=False) # Run headed to see what happens
        news_list = await scraper.scrape_important_news()
        
        print(f"\n📊 Total items scraped: {len(news_list)}")
        for item in news_list:
            print(f"  - [{item.get('type')}] {item.get('title')}")
            if item.get('type') != 'article':
                print(f"    ❌ ERROR: Type is {item.get('type')}, expected 'article'")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await scraper.close_browser()

if __name__ == "__main__":
    asyncio.run(test_scraper())
