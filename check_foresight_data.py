"""检查Foresight返回的数据结构"""
import asyncio
import sys
import json
sys.path.insert(0, 'crawler')

from scrapers.foresight import ForesightScraper

async def test():
    scraper = ForesightScraper()
    scraper.max_items = 2
    
    print("抓取Foresight新闻并检查数据结构...\n")
    news_list = await scraper.run()
    
    print(f"抓取到 {len(news_list)} 条新闻\n")
    print("=" * 80)
    
    for i, news in enumerate(news_list, 1):
        print(f"\n第 {i} 条新闻的完整数据结构:")
        print(json.dumps(news, indent=2, ensure_ascii=False, default=str))
        print("-" * 80)
        
        # 检查关键字段
        print(f"检查关键字段:")
        print(f"  'url' 字段: {news.get('url', '❌ 不存在')}")
        print(f"  'source_site' 字段: {news.get('source_site', '❌ 不存在')}")
        print(f"  'title' 字段: {news.get('title', '❌ 不存在')[:50] if news.get('title') else '❌ 不存在'}...")

asyncio.run(test())
