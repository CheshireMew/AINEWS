"""快速测试Foresight是否能成功保存"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.foresight import ForesightScraper
from database.db_sqlite import Database

async def test():
    scraper = ForesightScraper()
    scraper.max_items = 2
    
    print("测试Foresight修复...\n")
    news_list = await scraper.run()
    
    print(f"抓取到 {len(news_list)} 条新闻\n")
    
    # 检查数据完整性
    for i, news in enumerate(news_list, 1):
        print(f"{i}. {news['title'][:40]}...")
        print(f"   URL: {news.get('url', 'MISSING')}")
        print(f"   source_site: {news.get('source_site', 'MISSING')}")
        print(f"   published_at: {news.get('published_at', 'MISSING')}")
        print()
    
    # 尝试保存
    db = Database()
    saved = 0
    for news in news_list:
        if db.insert_news(news):
            saved += 1
            print(f"✅ 成功保存: {news['title'][:30]}...")
        else:
            print(f"❌ 保存失败: {news['title'][:30]}...")
    
    print(f"\n总结: {saved}/{len(news_list)} 条成功保存")

asyncio.run(test())
