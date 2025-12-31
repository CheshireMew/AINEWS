"""TheBlockBeats爬虫 - 使用样式检查"""
from .base import BaseScraper
from typing import List, Dict
from datetime import datetime

class BlockBeatsScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name='blockbeats',
            base_url='https://www.theblockbeats.info/newsflash'
        )
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取TheBlockBeats的重要新闻"""
        await self.fetch_page_with_delay(self.base_url)
        await self.page.wait_for_timeout(3000)
        
        # 点击"重要快讯"筛选
        try:
            important_checkbox = await self.page.query_selector('text=重要快讯')
            if important_checkbox:
                await self.page.evaluate("el => el.click()", important_checkbox)
                await self.page.wait_for_timeout(2000)
                print("[DEBUG] 已点击'只看精选'筛选")
        except Exception as e:
            print(f"点击筛选按钮失败: {e}")
        
        news_list = []
        processed_urls = set()
        
        # 获取所有新闻标题
        title_elements = await self.page.query_selector_all('.news-flash-title')
        print(f"[DEBUG] 找到 {len(title_elements)} 个新闻标题")
        
        for title_el in title_elements:
            try:
                # 检查是否有"first"徽章
                container = await title_el.evaluate_handle('el => el.closest(".news-flash-wrapper")')
                has_first_badge = await container.evaluate('''
                    el => {
                        return el.innerHTML.includes('first') || 
                               el.querySelector('img[src*="first"]') !== null;
                    }
                ''') if container else False
                
                # 样式检查（通用方法）
                style_check = await self.check_importance_by_style(title_el)
                
                # 只要满足任一条件即为重要
                if not (has_first_badge or style_check['is_important']):
                    continue
                
                # 提取信息
                title_text = await self.safe_extract_text(title_el)
                # 清理标题中的时间前缀 (e.g. "16:34 Some Title")
                import re
                title = re.sub(r'^\d{2}:\d{2}\s*', '', title_text).strip()
                
                url = await self.safe_get_attribute(title_el, 'href')
                
                if url and not url.startswith('http'):
                    url = f"https://www.theblockbeats.info{url}"

                if url in processed_urls:
                    continue
                processed_urls.add(url)

                
                # 提取时间 - BlockBeats的时间在标题文本开头（例如："08:31 新闻标题"）
                time_match = re.match(r'^(\d{2}:\d{2})', title_text)
                if time_match:
                    time_str = time_match.group(1)
                    # 解析为今天的时间
                    now = datetime.now()
                    hour, minute = map(int, time_str.split(':'))
                    published_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # 如果解析出的时间在未来，说明是昨天的新闻
                    if published_at > now:
                        from datetime import timedelta
                        published_at = published_at - timedelta(days=1)
                    
                    print(f"[DEBUG] 提取时间: {time_str} -> {published_at.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    # 如果没有匹配到时间，使用当前时间
                    print(f"[DEBUG] 未匹配到时间，title_text={title_text[:50]}")
                    published_at = datetime.now()
                
                # 确定重要标识
                if has_first_badge:
                    importance_flag = 'first_badge'
                else:
                    importance_flag = style_check['style_flag']
                
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
                    # BlockBeats的内容选择器
                    content_selectors = [
                        '.flash-content',  # BlockBeats快讯内容（正确选择器）
                        '.flash-content p',
                        '.flash-detail-content',
                        '.newsflash-content',
                        '.detail-content',
                    ]
                    content = await self.fetch_full_content(url, content_selectors)
                
                # 清理内容前缀
                content = self.clean_content(content, title)
                
                # 如果没获取到内容，使用标题作为fallback
                if not content or len(content) < 10:
                    content = title
                
                news_item = {
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_at': published_at.strftime('%Y-%m-%d %H:%M:%S'),  # 转换为字符串格式
                    'is_marked_important': True,
                    'site_importance_flag': importance_flag,
                    'author': self.site_name
                }
                
                news_list.append(news_item)
                print(f"[DEBUG] 添加重要新闻: {title[:30]}...")
                
            except Exception as e:
                print(f"解析BlockBeats新闻项失败: {e}")
                continue
        
        print(f"TheBlockBeats: 抓取到 {len(news_list)} 条重要新闻")
        return news_list


# 测试代码
if __name__ == '__main__':
    import asyncio
    
    async def test():
        scraper = BlockBeatsScraper()
        news = await scraper.run()
        
        for item in news[:3]:
            print(f"\n标题: {item['title']}")
            print(f"链接: {item['url']}")
            print(f"标识: {item['site_importance_flag']}")
    
    asyncio.run(test())
