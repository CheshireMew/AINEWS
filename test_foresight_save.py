"""快速测试Foresight URL修复"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.foresight import ForesightScraper
from database.db_sqlite import Database

async def test():
    scraper = ForesightScraper()
    scraper.max_items = 3
    
    print("测试Foresight URL修复...\n")
    news_list = await scraper.run()
    
    print(f"抓取到 {len(news_list)} 条新闻\n")
    
    # 尝试保存到数据库
    db = Database()
    saved = 0
    
    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news['title'][:40]}...")
        print(f"   URL: {news['url']}")
        
        result = db.insert_news(news)
        if result:
            print(f"   ✅ 成功保存，ID: {result}")
            saved += 1
        else:
            print(f"   ❌ 保存失败")
        print()
    
    print(f"\n总结: 抓取 {len(news_list)} 条，成功保存 {saved} 条")

asyncio.run(test())
