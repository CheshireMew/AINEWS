"""PANews爬虫 - 使用样式判断"""
from .base import BaseScraper
from typing import List, Dict
from datetime import datetime

class PANewsScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name='panews',
            base_url='https://www.panewslab.com/zh/newsflash'
        )
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取PANews的重要新闻"""
        await self.fetch_page_with_delay(self.base_url)
        await self.page.wait_for_timeout(3000)
        
        # 1. 点击"只看重要"筛选
        try:
            # 尝试多种方式找到按钮或 Label
            # 方式1: 文本匹配
            toggle_clicked = False
            
            # 查找包含"只看重要"的元素
            elements = await self.page.query_selector_all('text=只看重要')
            for el in elements:
                try:
                    # 检查是否是 label
                    tag = await el.evaluate('el => el.tagName')
                    if tag == 'LABEL':
                        await self.page.evaluate("el => el.click()", el)
                        toggle_clicked = True
                        break
                except:
                    continue
            
            if not toggle_clicked:
                 # 备用方案
                 btn = await self.page.query_selector('text=只看首发')
                 if btn:
                     is_checked = await btn.get_attribute('aria-checked')
                     if is_checked != 'true':
                         await self.page.evaluate("el => el.click()", btn)
                         toggle_clicked = True

            if toggle_clicked:
                await self.page.wait_for_timeout(2000)
                print("[DEBUG] 已尝试点击筛选")
            else:
                print("[DEBUG] 未找到筛选按钮，继续抓取")

        except Exception as e:
            print(f"点击筛选按钮失败: {e}")
        
        news_list = []
        
        # 2. 获取新闻列表
        # 增加对 /zh/ 的支持
        items = await self.page.query_selector_all('a[href*="/newsflash/"], a[href*="/article/"], a[href*="/zh/"]')
        
        print(f"[DEBUG] 找到 {len(items)} 个潜在新闻链接")
        
        processed_urls = set()
        
        for link in items:
            try:
                # 获取父容器
                container = await link.evaluate_handle('el => el.closest("div[data-slot=\'root\']") || el.closest("div.flex-col") || el.parentElement.parentElement')
                
                if not container:
                    continue

                # 3. 检查是否有"首发"标记
                # 任何 text 包含 "首发" 的元素
                has_shoufa = await container.evaluate('''
                    el => {
                        return el.innerText.includes('首发');
                    }
                ''')
                
                # 如果没有首发标记，暂时跳过
                if not has_shoufa:
                    # debugging
                    # text = await container.inner_text()
                    # print(f"Skip (no shoufa): {text[:20]}")
                    continue
                
                # 4. 提取链接和标题
                url = await self.safe_get_attribute(link, 'href')
                if not url:
                    continue
                    
                if not url.startswith('http'):
                    url = f"https://www.panewslab.com{url}"
                
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                
                title = await self.safe_extract_text(link)
                # 如果链接本身没文字，找找里面的 div 或 span
                if not title:
                     title = await link.inner_text()
                
                if not title or len(title) < 5:
                    continue

                # 5. 提取时间
                # 寻找任何看起来像时间的文本
                time_text = await container.evaluate('''
                    el => {
                        // 找 time 标签
                        const timeEl = el.querySelector('time');
                        if (timeEl) return timeEl.textContent;
                        
                        // 找 00:00 格式
                        const html = el.innerHTML;
                        const match = html.match(/\d{1,2}:\d{2}/);
                        if (match) return match[0];
                        
                        return '';
                    }
                ''')
                published_at = self.parse_relative_time(time_text) if time_text else datetime.now()
                
                # 6. 增量抓取
                if self.should_stop_scraping(title, url, published_at):
                    break
                
                # 7. 数量限制
                if len(news_list) >= self.max_items:
                    print(f"[数量限制] 已达到最大抓取数量 {self.max_items}，停止抓取")
                    break
                
                # 8. 获取完整内容
                content = ''
                # 8. 获取完整内容
                content = ''
                if url:
                    content = await self.fetch_full_content(
                        url,
                        content_selectors=['article.prose', 'article', '.article-content', '.content'],
                        extract_paragraphs=True
                    )
                
                # 清理内容
                content = self.clean_content(content, title)
               
                # Fallback
                if not content or len(content) < 10:
                    print(f"  [DEBUG] 使用fallback: content长度={len(content) if content else 0}")
                    content = title
                
                news_item = {
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_at': published_at,
                    'is_marked_important': True,
                    'site_importance_flag': 'shoufa'
                }
                
                news_list.append(news_item)
                print(f"[DEBUG] 添加重要新闻: {title[:20]}...")
                
            except Exception as e:
                print(f"解析PANews新闻项失败: {e}")
                continue
        
        print(f"PANews: 抓取到 {len(news_list)} 条重要新闻")
        return news_list
    
    async def extract_time_from_container(self, container) -> str:
        return ""


# 测试代码
if __name__ == '__main__':
    import asyncio
    
    async def test():
        scraper = PANewsScraper()
        news = await scraper.run()
        
        for item in news[:5]:
            print(f"\n标题: {item['title']}")
            print(f"标识: {item['site_importance_flag']}")
    
    asyncio.run(test())
