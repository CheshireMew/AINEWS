"""
ForesightNews 文章爬虫测试脚本
测试爬虫的基本功能
"""
import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'crawler'))

from scrapers.foresight_article import ForesightArticleScraper

async def main():
    print("="*70)
    print("ForesightNews 文章爬虫测试".center(70))
    print("="*70)
    print()
    
    # 1. 创建爬虫实例
    scraper = ForesightArticleScraper()
    print(f"✅ 爬虫实例创建成功: {scraper.site_name}")
    print(f"📚 专栏数量: {len(scraper.COLUMNS)}")
    for col in scraper.COLUMNS:
        print(f"   - {col['name']} ({col['url']})")
    print()
    
    # 2. 运行爬虫
    print("🚀 开始抓取文章...")
    print("-"*70)
    articles = await scraper.run()
    print("-"*70)
    print()
    
    # 3. 显示结果
    print(f"📊 抓取结果: 共 {len(articles)} 篇文章")
    print("="*70)
    print()
    
    if not articles:
        print("⚠️ 未抓取到任何文章")
        return
    
    # 4. 显示前5篇文章的详细信息
    print("前 5 篇文章详情:")
    print("="*70)
    
    for i, article in enumerate(articles[:5], 1):
        print(f"\n【文章 {i}】")
        print(f"  📰 标题: {article['title']}")
        print(f"  ✍️  作者: {article['author']}")
        print(f"  📁 类型: {article['type']}")
        print(f"  🕐 时间: {article['published_at']}")
        print(f"  🔗 链接: {article['url']}")
        print(f"  📝 内容长度: {len(article['content'])} 字符")
        print(f"  📄 内容预览: {article['content'][:120]}...")
    
    # 5. 统计信息
    print("\n" + "="*70)
    print("📈 统计信息:")
    print("="*70)
    
    # 按作者统计
    author_stats = {}
    for article in articles:
        author = article.get('author', 'Unknown')
        author_stats[author] = author_stats.get(author, 0) + 1
    
    print("\n按专栏统计:")
    for author, count in sorted(author_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {author}: {count} 篇")
    
    # 验证必需字段
    print("\n字段验证:")
    required_fields = ['title', 'author', 'content', 'url', 'type', 'published_at']
    all_valid = True
    for field in required_fields:
        has_field = all(field in article for article in articles)
        status = "✅" if has_field else "❌"
        print(f"  {status} {field}: {'全部包含' if has_field else '缺失'}")
        all_valid = all_valid and has_field
    
    # 验证 type='article'
    type_check = all(article.get('type') == 'article' for article in articles)
    status = "✅" if type_check else "❌"
    print(f"  {status} type='article': {'全部正确' if type_check else '有误'}")
    all_valid = all_valid and type_check
    
    print("\n" + "="*70)
    if all_valid:
        print("✅ 所有测试通过！".center(70))
    else:
        print("❌ 部分测试失败".center(70))
    print("="*70)

if __name__ == '__main__':
    asyncio.run(main())
