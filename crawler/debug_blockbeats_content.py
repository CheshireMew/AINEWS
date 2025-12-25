"""调试BlockBeats内容选择器"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from scrapers.blockbeats import BlockBeatsScraper
from scrapers.base import BaseScraper

# 重写fetch_full_content来调试
class DebugBlockBeatsScraper(BlockBeatsScraper):
    async def debug_fetch_content(self, url):
        """调试模式：测试不同选择器"""
        print(f"\n{'='*80}")
        print(f"调试URL: {url}")
        print(f"{'='*80}\n")
        
        await self.page.goto(url)
        await self.page.wait_for_timeout(3000)
        
        # 测试各种选择器
        selectors = [
            '.flash-content',
            '.flash-detail-content',
            '.newsflash-detail-content',
            '.newsflash-content',
            '.detail-content',
            '.content',
            '.article-content',
            '[class*="flash"][class*="content"]',
            'article',
            '.post-content',
        ]
        
        print("测试不同选择器:\n")
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    text = text.strip()
                    if len(text) > 20:
                        print(f"✅ {selector:40s} → {len(text):4d} 字")
                        print(f"   预览: {text[:80]}...")
                        print()
                    else:
                        print(f"⚠️ {selector:40s} → 太短({len(text)}字)")
                else:
                    print(f"❌ {selector:40s} → 未找到")
            except Exception as e:
                print(f"❌ {selector:40s} → 错误: {e}")
        
        # 查找所有可能的内容容器
        print(f"\n{'='*80}")
        print("查找包含长文本的DIV:")
        print(f"{'='*80}\n")
        
        long_divs = await self.page.evaluate('''() => {
            const divs = document.querySelectorAll('div');
            const result = [];
            divs.forEach(div => {
                const text = div.innerText.trim();
                if (text.length > 100) {
                    const classes = div.className || '';
                    const id = div.id || '';
                    result.push({
                        selector: classes ? '.' + classes.split(' ')[0] : (id ? '#' + id : 'div'),
                        length: text.length,
                        preview: text.substring(0, 50)
                    });
                }
            });
            return result.slice(0, 10);  // 只返回前10个
        }''')
        
        for item in long_divs:
            print(f"选择器: {item['selector']}")
            print(f"长度: {item['length']} 字")
            print(f"预览: {item['preview']}...")
            print()

async def main():
    scraper = DebugBlockBeatsScraper()
    
    try:
        await scraper.init_browser()
        
        # 先抓取列表获取一个URL
        print("先抓取列表页获取新闻URL...")
        news_list = await scraper.scrape_important_news()
        
        if not news_list:
            print("未抓到新闻，无法继续测试")
            return
        
        # 测试第一个URL
        first_url = news_list[0]['url']
        await scraper.debug_fetch_content(first_url)
        
    finally:
        await scraper.close()

if __name__ == '__main__':
    asyncio.run(main())
