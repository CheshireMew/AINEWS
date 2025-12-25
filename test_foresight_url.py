"""详细测试Foresight URL"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.foresight import ForesightScraper

async def test():
    scraper = ForesightScraper()
    scraper.max_items = 5
    
    print("开始抓取Foresight新闻并检查URL...\n")
    news_list = await scraper.run()
    
    print(f"\n抓取到 {len(news_list)} 条新闻\n")
    print("=" * 80)
    
    for i, news in enumerate(news_list, 1):
        print(f"\n{i}. 标题: {news.get('title', 'NO TITLE')[:60]}")
        print(f"   完整URL: {news.get('url', 'NO URL')}")
        print(f"   来源: {news.get('source_site', 'NO SOURCE')}")
        
    print("\n" + "=" * 80)
    
    # 检查数据库中是否有这些URL
    import sqlite3
    conn = sqlite3.connect('ainews.db')
    c = conn.cursor()
    
    print("\n检查数据库中是否存在这些URL:\n")
    for i, news in enumerate(news_list, 1):
        url = news.get('url')
        c.execute('SELECT source_site, title FROM news WHERE source_url = ?', (url,))
        existing = c.fetchone()
        
        if existing:
            print(f"{i}. ❌ URL已存在!")
            print(f"   来源: {existing[0]}")
            print(f"   标题: {existing[1][:60]}")
        else:
            print(f"{i}. ✅ URL不存在，可以保存")
            
    conn.close()

asyncio.run(test())
