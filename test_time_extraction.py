"""测试Foresight时间提取"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.foresight import ForesightScraper

async def test():
    scraper = ForesightScraper()
    scraper.max_items = 3
    
    print("测试Foresight时间提取...\n")
    news_list = await scraper.run()
    
    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news['title'][:40]}...")
        print(f"   发布时间: {news.get('published_at')}")
        print()
    
    print(f"✅ 成功抓取 {len(news_list)} 条，时间提取正常")

asyncio.run(test())
