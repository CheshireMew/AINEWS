"""
Odaily 文章爬虫
Target: https://www.odaily.news/zh-CN/post
"""
from scrapers.article_base import ArticleScraper
from typing import List, Dict, Optional
import asyncio
import re

class OdailyArticleScraper(ArticleScraper):
    """Odaily 深度文章爬虫"""
    
    def __init__(self):
        super().__init__('Odaily Article', 'https://www.odaily.news', max_items=20)
        self.base_url = 'https://www.odaily.news'
        self.list_url = 'https://www.odaily.news/zh-CN/post'
    
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
                # 链接 href 包含 /zh-CN/post/ 的 a 标签
                await self.page.wait_for_selector('a[href*="/zh-CN/post/"]', timeout=10000)
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
        
        # 查找所有文章链接
        # 策略：找到包含 /zh-CN/post/ 数字ID 的链接
        # href 例如: /zh-CN/post/5208487
        link_elems = await self.page.query_selector_all('a[href*="/zh-CN/post/"]')
        print(f"找到 {len(link_elems)} 个潜在链接")
        
        processed_urls = set()
        
        for link in link_elems:
            try:
                href = await link.get_attribute('href')
                if not href or '/post/' not in href:
                    continue
                    
                # 简单的去重（避免同一个链接多次出现）
                if href in processed_urls:
                    continue
                processed_urls.add(href)
                
                full_url = self.base_url + href if href.startswith('/') else href
                
                # Title: 链接内的 span
                title_elem = await link.query_selector('span')
                if not title_elem:
                    # 尝试直接获取 text
                    title_text = await link.text_content()
                else:
                    title_text = await title_elem.text_content()
                
                if not title_text:
                    continue
                title = title_text.strip()
                
                # Summary: 链接父级的兄弟元素
                # HTML结构:
                # <div>
                #   <a href="...">...</a>
                #   <div class="mt-[4px] ...">摘要内容</div>
                # </div>
                # 所以我们要找 link 的下一个兄弟 div
                summary = ""
                # Playwright 没有直接的 "next_sibling" 选择器，得用 xpath 或者 eval
                # 这里尝试用 evaluate 获取下一个兄弟元素的文本
                summary = await self.page.evaluate("""(element) => {
                    const next = element.nextElementSibling;
                    return next ? next.textContent : "";
                }""", link)
                
                summary = summary.strip()
                
                # 列表页没有准确的时间（只有日期），去详情页拿
                
                # 检查增量抓取
                if self.should_stop_scraping(title, full_url):
                    print(f"  [增量抓取] 停止: {title}")
                    break
                
                # 进入详情页
                details = await self._fetch_article_details(full_url)
                
                if details:
                    published_at = details.get('published_at')
                    author = details.get('author') or 'Odaily'
                    
                    # 用户要求：摘要作为数据内容
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

    async def _fetch_article_details(self, url: str) -> Optional[Dict]:
        """获取文章详情"""
        page = await self.browser.new_page()
        try:
            await self.fetch_page_with_delay(url, page=page)
            await asyncio.sleep(2)
            
            # Author: 查找 href 包含 /author/ 的链接
            author = "Odaily"
            try:
                author_elem = await page.query_selector('a[href*="/author/"]')
                if author_elem:
                    author = await author_elem.text_content()
                    author = author.strip()
            except:
                pass
            
            # Time: 查找日期时间格式的文本
            # 结构: <div class="...">2025-12-31 12:20</div>
            # 策略：找到文本匹配日期格式的元素
            published_at = None
            try:
                # 尝试通过文本内容查找
                # 也可以尝试定位：.flex.flex-col.justify-end.items-end > div
                time_elem = await page.query_selector('div.flex.flex-col.justify-end.items-end > div')
                if time_elem:
                    time_text = await time_elem.text_content()
                    if re.search(r'\d{4}-\d{2}-\d{2}', time_text):
                        published_at = time_text.strip()
            except:
                pass
            
            return {
                'author': author,
                'published_at': published_at
            }
            
        except Exception as e:
            print(f"    ⚠️ 详情页加载失败: {e}")
            return None
        finally:
            await page.close()
