"""MarsBit爬虫 - 使用样式判断"""
from .base import BaseScraper
from typing import List, Dict
from datetime import datetime

class MarsBitScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name='marsbit',
            base_url='https://news.marsbit.co/flash'
        )
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取MarsBit的重要新闻"""
        await self.fetch_page_with_delay(self.base_url)
        await self.page.wait_for_timeout(3000)
        
        # 点击"只要重要快讯"复选框
        try:
            important_checkbox = await self.page.query_selector('.flash-only-important input[type="checkbox"]')
            if important_checkbox:
                # 检查是否已经选中
                is_checked = await important_checkbox.is_checked()
                if not is_checked:
                    await self.page.evaluate("el => el.click()", important_checkbox)
                    await self.page.wait_for_timeout(2000)
                    print("[DEBUG] 已点击'只要重要快讯'筛选")
        except Exception as e:
            print(f"点击筛选按钮失败: {e}")
        
        news_list = []
        
        # 获取所有带有 "item-icons import" 类的重要新闻容器
        important_items = await self.page.query_selector_all('.item-icons.import')
        print(f"[DEBUG] 找到 {len(important_items)} 个重要新闻")
        
        processed_urls = set()
        
        for item in important_items:
            try:
                # 从容器中找到新闻链接（通常在父元素或相邻元素中）
                container = await item.evaluate_handle('el => el.closest(".flash-item") || el.parentElement')
                if not container:
                    continue
                
                # 在容器中查找链接
                link = await container.query_selector('a[href*="/flash/"]')
                if not link:
                    continue
                
                url = await self.safe_get_attribute(link, 'href')
                if not url or 'flash' not in url:
                    continue
                
                if url in processed_urls:
                    continue
                
                # 提取标题
                title = await self.safe_extract_text(link)
                if not title or len(title) < 10:
                    continue
                
                if url and not url.startswith('http'):
                    url = f"https://news.marsbit.co{url}"
                
                processed_urls.add(url)
                
                # 从 item-icons import 元素中提取时间
                time_text = ''
                try:
                    time_el = await item.query_selector('.time-left')
                    if time_el:
                        time_text = await self.safe_extract_text(time_el)
                except:
                    pass
                
                published_at = self.parse_relative_time(time_text) if time_text else datetime.now()
                
                # 增量抓取：检查是否已经抓到上次的新闻
                if self.should_stop_scraping(title, url, published_at):
                    break  # 停止抓取
                
                # 数量限制：检查是否已达到最大抓取数量
                if len(news_list) >= self.max_items:
                    print(f"[数量限制] 已达到最大抓取数量 {self.max_items}，停止抓取")
                    break
                
                # 获取完整内容
                content = ''
                if url:
                    # MarsBit的内容选择器
                    content_selectors = [
                        '.content-words',  # MarsBit快讯内容（正确选择器）
                        '.flash-content',
                        '.article-content',
                    ]
                    content = await self.fetch_full_content(url, content_selectors)
                
                # 如果没获取到内容，使用标题作为fallback
                if not content or len(content) < 10:
                    content = title
                
                # 清理内容
                content = self.clean_content(content, title)
                
                news_item = {
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_at': published_at,
                    'is_marked_important': True,
                    'site_importance_flag': 'import_icon',  # MarsBit使用import类标记重要
                    'author': self.site_name
                }
                
                news_list.append(news_item)
                
            except Exception as e:
                continue
        
        print(f"MarsBit: 抓取到 {len(news_list)} 条重要新闻")
        return news_list
    
    async def extract_time_from_container(self, container) -> str:
        """从容器中提取时间"""
        try:
            time_str = await container.evaluate('''
                el => {
                    const timeEl = el.querySelector('[class*="time"]') || 
                                   el.querySelector('span');
                    return timeEl ? timeEl.textContent : '';
                }
            ''')
            return time_str
        except:
            return ""


if __name__ == '__main__':
    import asyncio
    
    async def test():
        scraper = MarsBitScraper()
        news = await scraper.run()
        
        for item in news[:5]:
            print(f"\n标题: {item['title']}")
            print(f"URL: {item['url']}")
            print(f"内容长度: {len(item['content'])} 字符")
            print(f"内容预览: {item['content'][:100]}...")
            print(f"标识: {item['site_importance_flag']}")
    
    asyncio.run(test())
