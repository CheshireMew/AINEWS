"""分析BlockBeats详情页结构"""
import asyncio
from playwright.async_api import async_playwright

async def analyze_blockbeats_detail():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 访问列表页
        print("访问BlockBeats列表页...")
        await page.goto('https://www.theblockbeats.info/newsflash')
        await page.wait_for_timeout(3000)
        
        #点击"重要快讯"筛选
        try:
            filter_btn = await page.query_selector('text=重要快讯')
            if filter_btn:
                await filter_btn.click()
                print("点击筛选按钮成功")
                await page.wait_for_timeout(2000)
        except:
            pass
        
        # 获取第一个新闻链接
        title_elements = await page.query_selector_all('.news-flash-title')
        if not title_elements:
            print("未找到新闻标题")
            await browser.close()
            return
        
        first_title = title_elements[0]
        url = await first_title.get_attribute('href')
        if not url.startswith('http'):
            url = f"https://www.theblockbeats.info{url}"
        
        print(f"\n访问详情页: {url}")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        
       # 分析详情页结构
        print("\n=== 分析详情页DOM结构 ===\n")
        
        # 检查常见的内容选择器
        selectors_to_test = [
            '.flash-content',
            '.flash-detail-content',
            '.newsflash-detail-content',
            '.newsflash-content',
            '.detail-content',
            '.content',
            '.article-content',
            '[class*="content"]',
            '[class*="detail"]',
            '[class*="flash"]',
        ]
        
        for selector in selectors_to_test:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    text = text.strip()
                    if len(text) > 20:  # 至少有一定长度
                        print(f"✅ 找到: {selector}")
                        print(f"   内容长度: {len(text)} 字")
                        print(f"   内容预览: {text[:100]}...")
                        print()
            except:
                pass
        
        # 获取所有class包含content的元素
        print("\n=== 包含'content'的class ===")
        content_classes = await page.evaluate('''() => {
            const elements = document.querySelectorAll('[class*="content"]');
            const classes = new Set();
            elements.forEach(el => {
                el.className.split(' ').forEach(c => {
                    if (c.includes('content')) classes.add(c);
                });
            });
            return Array.from(classes);
        }''')
        for cls in content_classes:
            print(f"   .{cls}")
        
        # 获取所有class包含detail的元素
        print("\n=== 包含'detail'的class ===")
        detail_classes = await page.evaluate('''() => {
            const elements = document.querySelectorAll('[class*="detail"]');
            const classes = new Set();
            elements.forEach(el => {
                el.className.split(' ').forEach(c => {
                    if (c.includes('detail')) classes.add(c);
                });
            });
            return Array.from(classes);
        }''')
        for cls in detail_classes:
            print(f"   .{cls}")
        
        input("\n按Enter键关闭浏览器...")
        await browser.close()

if __name__ == '__main__':
    asyncio.run(analyze_blockbeats_detail())
