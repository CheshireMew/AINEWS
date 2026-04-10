"""
MarsBit 文章爬虫
Target: https://www.marsbit.co/
"""
from .article_base import ArticleScraper
from typing import List, Dict, Optional
import asyncio
from datetime import datetime

class MarsBitArticleScraper(ArticleScraper):
    """MarsBit 深度文章爬虫"""
    
    def __init__(self):
        super().__init__('MarsBit Article', 'https://www.marsbit.co/', max_items=20)
        self.base_url = 'https://www.marsbit.co'
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取最新文章"""
        all_articles = []
        
        try:
            print(f"\n正在访问: {self.base_url}")
            await self.fetch_page_with_delay(self.base_url)
            await asyncio.sleep(3)
            
            # 抓取列表文章
            try:
                # 等待列表元素加载 .news-list-item
                await self.page.wait_for_selector('.news-list-item', timeout=10000)
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
        
        # 查找文章容器
        items = await self.page.query_selector_all('.news-list-item')
        print(f"找到 {len(items)} 个列表项")
        
        for item in items:
            try:
                # 1. 提取标题和链接
                title_link = await item.query_selector('a.title-synopsis')
                if not title_link:
                    continue
                
                title = await title_link.get_attribute('title')
                href = await title_link.get_attribute('href')
                
                if not title or not href:
                    continue
                    
                full_url = href if href.startswith('http') else self.base_url + href
                
                # 检查增量抓取
                if self.should_stop_scraping(title, full_url):
                    print(f"  [增量抓取] 停止: {title}")
                    break
                
                # 2. 列表页提取作者 (备用)
                list_author = "MarsBit"
                try:
                    author_elem = await item.query_selector('.author-time a')
                    if author_elem:
                        list_author = await author_elem.text_content()
                except:
                    pass

                # 3. 进入详情页获取正文和准确作者
                details = await self._fetch_article_details(full_url)
                
                if details:
                    # 使用抓取时的当前时间作为发布时间（用户要求）
                    published_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 优先使用详情页作者
                    author = details.get('author') or list_author
                    content = details.get('content', '')
                    
                    articles.append({
                        'title': title,
                        'content': content,
                        'url': full_url,
                        'published_at': published_at,
                        'source_site': self.site_name,
                        'author': author,
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
            
            # Author: .news-info .author
            author = None
            try:
                author_elem = await page.query_selector('.news-info .author')
                if author_elem:
                    author = await author_elem.text_content()
            except:
                pass
            
            # Content: .news-synopsis p (用户指定摘要作为内容)
            content = ""
            try:
                # 优先尝试 .news-synopsis
                synopsis_elem = await page.query_selector('.news-synopsis')
                if synopsis_elem:
                    content = await synopsis_elem.inner_text()
                
                # 如果没有，尝试找真正的正文 .news-details-content
                if not content or len(content) < 10:
                     content_main = await page.query_selector('.news-details-content')
                     if content_main:
                         # 移除 info 和 title 部分，只取正文文本？
                         # 简单起见直接取整个 inner_text，虽然会包含标题和作者，但能保证不漏
                         content = await content_main.inner_text()
            except:
                pass
            
            return {
                'author': author,
                'content': content
            }
            
        except Exception as e:
            print(f"    ⚠️ 详情页加载失败: {e}")
            return None
        finally:
            await page.close()