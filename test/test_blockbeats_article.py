"""测试 BlockBeats 文章爬虫"""
import sys
sys.path.insert(0, 'crawler')

import asyncio
from scrapers.blockbeats_article import BlockBeatsArticleScraper


async def test():
    print("="*70)
    print("测试 BlockBeats 文章爬虫")
    print("="*70)
    
    scraper = BlockBeatsArticleScraper()
    await scraper.init_browser(headless=True)
    try:
        articles = await scraper.scrape_important_news()
    finally:
        await scraper.close_browser()
    
    print(f"\n{'='*70}")
    print(f"总计抓取: {len(articles)} 篇文章")
    print(f"{'='*70}")
    
    for i, article in enumerate(articles[:5], 1):  # 只显示前5篇
        print(f"\n{i}. {article['title']}")
        print(f"   URL: {article['url']}")
        print(f"   作者: {article['author']}")
        print(f"   时间: {article['published_at']}")
        print(f"   类型: {article['type']}")
        print(f"   标记: {article['site_importance_flag']}")
        print(f"   摘要: {article['content'][:150]}...")
    
    # 验证字段
    print(f"\n{'='*70}")
    print("字段验证:")
    if articles:
        first = articles[0]
        print(f"  ✓ title: {bool(first.get('title'))}")
        print(f"  ✓ url: {bool(first.get('url'))}")
        print(f"  ✓ content: {len(first.get('content', ''))} 字")
        print(f"  ✓ author: {first.get('author')}")
        print(f"  ✓ type: {first.get('type')}")
        print(f"  ✓ published_at: {first.get('published_at')}")


if __name__ == '__main__':
    import contextlib
    with open('test_output.log', 'w', encoding='utf-8') as f:
        with contextlib.redirect_stdout(f):
            asyncio.run(test())
