"""测试Foresight爬虫"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.foresight import ForesightScraper

async def test():
    scraper = ForesightScraper()
    scraper.max_items = 3
    
    print("开始测试Foresight爬虫...")
    try:
        news_list = await scraper.run()
        print(f"\n成功抓取 {len(news_list)} 条新闻")
        
        for i, news in enumerate(news_list, 1):
            print(f"\n{i}. {news.get('title', 'NO TITLE')[:50]}")
            print(f"   URL: {news.get('url', 'NO URL')[:60]}")
            print(f"   重要: {news.get('is_marked_important', False)}")
            
    except Exception as e:
        import traceback
        print(f"\n错误: {e}")
        traceback.print_exc()

asyncio.run(test())
