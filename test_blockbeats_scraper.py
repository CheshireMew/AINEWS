"""直接运行 BlockBeats 爬虫，查看原始抓取内容"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.blockbeats import BlockBeatsScraper

async def test():
    scraper = BlockBeatsScraper()
    scraper.max_items = 2  # 只抓2条
    
    print("开始抓取 BlockBeats...")
    news_list = await scraper.run()
    
    print(f"\n抓取到 {len(news_list)} 条新闻\n")
    
    for i, item in enumerate(news_list, 1):
        print(f"{'='*80}")
        print(f"新闻 #{i}")
        print(f"标题: {item['title'][:50]}...")
        print(f"\n内容统计:")
        content = item['content']
        print(f"  长度: {len(content)} 字符")
        print(f"  换行符数: {content.count(chr(10))}")
        print(f"  双换行数: {content.count(chr(10)*2)}")
        print(f"  三换行数: {content.count(chr(10)*3)}")
        print(f"  四换行数: {content.count(chr(10)*4)}")
        
        print(f"\n内容 (repr, 前200字符):")
        print(repr(content[:200]))
        
        print(f"\n内容 (显示, 前300字符):")
        print(content[:300])
        print(f"{'='*80}\n")

if __name__ == '__main__':
    asyncio.run(test())
