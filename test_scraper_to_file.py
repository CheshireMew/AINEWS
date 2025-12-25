"""测试爬虫返回的原始内容"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.blockbeats import BlockBeatsScraper

async def test():
    scraper = BlockBeatsScraper()
    scraper.max_items = 1  # 只抓1条
    
    news_list = await scraper.run()
    
    if news_list:
        item = news_list[0]
        content = item['content']
        
        # 写入文件
        with open('raw_content.txt', 'w', encoding='utf-8') as f:
            f.write("=== 内容 repr ===\n")
            f.write(repr(content))
            f.write("\n\n=== 统计 ===\n")
            f.write(f"总长度: {len(content)}\n")
            f.write(f"换行符(\\n): {content.count(chr(10))}\n")
            f.write(f"双换行(\\n\\n): {content.count(chr(10)*2)}\n")
            f.write(f"三换行(\\n\\n\\n): {content.count(chr(10)*3)}\n")
            f.write(f"四换行(\\n\\n\\n\\n): {content.count(chr(10)*4)}\n")
            f.write("\n=== 内容显示 ===\n")
            f.write(content)
        
        print("✅ 内容已写入 raw_content.txt")
    else:
        print("❌ 未抓取到新闻")

asyncio.run(test())
