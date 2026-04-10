"""
PANews 文章爬虫
Target: https://www.panewslab.com/zh/in-depth
"""
from .article_base import ArticleScraper
from typing import List, Dict, Optional
import asyncio
import re
from datetime import datetime, timedelta

class PANewsArticleScraper(ArticleScraper):
    """PANews 深度文章爬虫"""
    
    def __init__(self):
        super().__init__('PANews Article', 'https://www.panewslab.com', max_items=20)
        self.base_url = 'https://www.panewslab.com'
        self.list_url = 'https://www.panewslab.com/zh/in-depth'
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取最新文章"""
        all_articles = []
        
        try:
            print(f"\n正在访问: {self.list_url}")
            # PANews 可能需要等待网络加载
            await self.fetch_page_with_delay(self.list_url)
            await asyncio.sleep(4)
            
            # 抓取列表文章
            try:
                # 等待列表链接出现
                await self.page.wait_for_selector('a[href^="/zh/articles/"]', timeout=15000)
            except:
                print("⚠️ 等待列表元素超时")

            all_articles = await self._scrape_list_articles()
            print(f"📋 抓取到: {len(all_articles)} 篇文章")
            
            # 应用限制
            if len(all_articles) > self.max_items:
                all_articles = all_articles[:self.max_items]
        
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            import traceback
            traceback.print_exc()
        
        return all_articles

    async def _scrape_list_articles(self) -> List[Dict]:
        """抓取列表文章"""
        articles = []
        
        # 查找所有文章容器（根据用户提供的结构，文章包裹在 space-y-2 的 div 中，或者直接找链接）
        # 这里尝试直接找标题链接，然后向上/同级查找其他元素
        
        # 更好的方式是查找每个文章块。
        # 用户给出的结构显示： <div class="w-full space-y-2"> 是文章主体的容器
        items = await self.page.query_selector_all('.w-full.space-y-2')
        print(f"找到 {len(items)} 个文章块")
        
        for item in items:
            try:
                # 1. 标题和链接
                # 链接类名包含 line-clamp-2
                title_link = await item.query_selector('a[href^="/zh/articles/"].line-clamp-2')
                if not title_link:
                    continue
                
                href = await title_link.get_attribute('href')
                title = await title_link.text_content()
                if title:
                    title = title.strip()
                if not href or not title:
                    continue
                    
                full_url = self.base_url + href if href.startswith('/') else href
                
                # 2. 摘要 (Summary as Content)
                # 也是个链接，类名 text-neutrals-60 line-clamp-3
                summary = ""
                summary_elem = await item.query_selector('a[href^="/zh/articles/"].text-neutrals-60')
                if summary_elem:
                    summary = await summary_elem.text_content()
                    summary = summary.strip()
                
                # 3. 作者和时间
                # 包裹在 flex-row items-center justify-start gap-5 中
                author = "PANews"
                published_at = None
                
                meta_div = await item.query_selector('.flex.flex-row.items-center.justify-start.gap-5')
                if meta_div:
                    # 作者: a href="/zh/columns/..."
                    author_elem = await meta_div.query_selector('a[href^="/zh/columns/"]')
                    if author_elem:
                        author = await author_elem.text_content()
                        author = author.strip()
                    
                    # 时间: span text-neutrals-40
                    time_elem = await meta_div.query_selector('span.text-neutrals-40')
                    if time_elem:
                        time_str = await time_elem.text_content()
                        time_str = time_str.strip()
                        published_at = self._parse_relative_time(time_str)
                
                # 检查增量抓取
                if self.should_stop_scraping(title, full_url):
                    print(f"  [增量抓取] 停止: {title}")
                    break
                
                # PANews 列表页信息很全，不需要进详情页（且用户要求用列表摘要当正文）
                # 除非列表页取不到时间
                if not published_at:
                    published_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                content = summary
                
                articles.append({
                    'title': title,
                    'content': content,
                    'url': full_url,
                    'published_at': published_at,
                    'source_site': self.site_name,
                    'author': author,
                    'summary': summary,
                    'type': self.news_type
                })
                print(f"  ✅ 抓取成功: {title} ({author})")
                
            except Exception as e:
                print(f"  ⚠️ 处理单条失败: {e}")
                continue
                
        return articles

    def _parse_relative_time(self, time_str: str) -> str:
        """解析相对时间，如 '39分钟前', '2小时前'"""
        now = datetime.now()
        try:
            time_str = time_str.replace(' ', '')
            if '分钟前' in time_str:
                minutes = int(re.search(r'(\d+)分钟前', time_str).group(1))
                pub_time = now - timedelta(minutes=minutes)
                return pub_time.strftime('%Y-%m-%d %H:%M:%S')
            elif '小时前' in time_str:
                hours = int(re.search(r'(\d+)小时前', time_str).group(1))
                pub_time = now - timedelta(hours=hours)
                return pub_time.strftime('%Y-%m-%d %H:%M:%S')
            elif '天前' in time_str:
                days = int(re.search(r'(\d+)天前', time_str).group(1))
                pub_time = now - timedelta(days=days)
                return pub_time.strftime('%Y-%m-%d %H:%M:%S')
            elif '刚刚' in time_str:
                 return now.strftime('%Y-%m-%d %H:%M:%S')
            elif re.match(r'\d{4}-\d{2}-\d{2}', time_str):
                # 已经是日期格式
                return time_str
            else:
                return now.strftime('%Y-%m-%d %H:%M:%S')
        except:
             return now.strftime('%Y-%m-%d %H:%M:%S')

    async def _fetch_article_details(self, url: str) -> Optional[Dict]:
        """PANews 列表页信息足够，通常不需要进详情页"""
        return None
