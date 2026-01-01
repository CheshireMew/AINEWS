"""
ChainCatcher 文章爬虫（使用 Playwright）
抓取 ChainCatcher 深度文章
"""

from .article_base import ArticleScraper
from typing import List, Dict, Optional
import asyncio
import re

class ChainCatcherArticleScraper(ArticleScraper):
    """ChainCatcher 文章爬虫"""
    
    def __init__(self):
        super().__init__('ChainCatcher Article', 'https://www.chaincatcher.com', max_items=20)
        self.base_url = 'https://www.chaincatcher.com'
        self.list_url = 'https://www.chaincatcher.com/article'
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取最新文章"""
        all_articles = []
        
        try:
            print(f"\n正在访问: {self.list_url}")
            await self.fetch_page_with_delay(self.list_url)
            await asyncio.sleep(3)
            
            # 抓取列表文章
            try:
                # 等待列表元素加载
                await self.page.wait_for_selector('.article_wraper', timeout=10000)
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
        
        # 查找文章容器 (List Page)
        # 结构: .items.pb-2 -> .article_wraper
        items = await self.page.query_selector_all('.items')
        
        print(f"找到 {len(items)} 个列表项")
        
        for item in items:
            try:
                # 1. 提取标题和链接
                title_elem = await item.query_selector('.article_title_span')
                link_elem = await item.query_selector('a.content') # 链接容器
                
                if not title_elem or not link_elem:
                    continue
                
                title = await title_elem.text_content()
                title = title.strip()
                href = await link_elem.get_attribute('href')
                
                if not title or not href:
                    continue
                    
                full_url = self.base_url + href if href.startswith('/') else href
                
                # 2. 提取摘要（List Page）
                summary = ""
                summary_elem = await item.query_selector('.article_content.small_article')
                if summary_elem:
                    summary = await summary_elem.text_content()
                    summary = summary.strip()

                # 3. 提取列表页隐藏时间 (e.g. 2025-12-31 12:41:28)
                publish_time = None
                time_elem = await item.query_selector('.hiddenTime')
                if time_elem:
                    raw_time = await time_elem.text_content()
                    publish_time = raw_time.strip()
                
                # 检查增量抓取
                if self.should_stop_scraping(title, full_url):
                    print(f"  [增量抓取] 停止: {title}")
                    break
                
                # 4. 获取详情页信息 (作者、正文、更准确的时间)
                details = await self._fetch_article_details(full_url)
                
                if details:
                    # 如果详情页有更准确的时间/作者，覆盖之
                    if details.get('author'):
                        author = details['author']
                    else:
                        author = 'ChainCatcher'
                        
                    content = details.get('content', '') or summary
                    
                    # 优先使用详情页时间，如果缺失则使用列表页时间
                    published_at = details.get('published_at') or publish_time
                    
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

    async def _fetch_article_details(self, url: str) -> Optional[Dict]:
        """获取文章详情"""
        page = await self.browser.new_page()
        try:
            await self.fetch_page_with_delay(url, page=page)
            await asyncio.sleep(1)
            
            # Author: .information .name
            author = "ChainCatcher"
            try:
                author_elem = await page.query_selector('.information .name')
                if author_elem:
                    author = await author_elem.text_content()
                    author = author.strip()
            except:
                pass
            
            # Time: .information .time
            published_at = None
            try:
                time_elem = await page.query_selector('.information .time')
                if time_elem:
                    published_at = await time_elem.text_content()
                    published_at = published_at.strip()
            except:
                pass
            
            # Content
            # 用户提到 ".article_content ... 我们就当作数据的内容"
            # 如果这是指直接用摘要当内容，那我们已经在 list articles 里拿到了。
            # 但通常我们需要全文。尝试找几个常见的正文容器。
            content = ""
            try:
                # 尝试通用选择器
                # 用户没有给正文的选择器，但给了摘要的选择器 .article_content (在列表页)
                # 在详情页通常也有 .article_content 或 ID="content"
                content_elem = await page.query_selector('.article_content') or \
                               await page.query_selector('#content') or \
                               await page.query_selector('.main-content')
                               
                if content_elem:
                    content = await content_elem.inner_text()
            except:
                pass
            
            return {
                'author': author,
                'published_at': published_at,
                'content': content
            }
            
        except Exception as e:
            print(f"    ⚠️ 详情页加载失败: {e}")
            return None
        finally:
            await page.close()
