"""
Chainfeeds Article Scraper (RSS)
Target: https://www.chainfeeds.me/rss
"""
from scrapers.article_base import ArticleScraper
from typing import List, Dict, Optional
import asyncio
from datetime import datetime, timedelta, timezone
import re
from bs4 import BeautifulSoup

class ChainfeedsArticleScraper(ArticleScraper):
    """Chainfeeds RSS 爬虫"""
    
    def __init__(self):
        super().__init__('Chainfeeds Article', 'https://www.chainfeeds.xyz', max_items=20)
        self.rss_url = 'https://www.chainfeeds.me/rss'
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取最新文章 (RSS)"""
        all_articles = []
        
        try:
            print(f"\n正在访问 RSS: {self.rss_url}")
            # RSS content implies XML
            # Use fetch_page_with_delay with return_response=True
            response = await self.fetch_page_with_delay(self.rss_url, return_response=True)
            if not response:
                print("❌ RSS 请求返回 None")
                return []
                
            await asyncio.sleep(2)
            
            # Use raw response text for XML, as page.content() might be rendered HTML
            xml_content = await response.text()
            
            # Suppress XML warning since we're using html.parser intentionally
            from bs4 import XMLParsedAsHTMLWarning
            import warnings
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            
            # Use html.parser as lxml might not be installed
            soup = BeautifulSoup(xml_content, 'html.parser')
            
            # Try to find entries
            entries = soup.find_all('entry')
            if not entries:
                # Retry with html parser if xml failed (browser might have rendered it)
                soup = BeautifulSoup(xml_content, 'html.parser')
                entries = soup.find_all('entry')
            
            print(f"📋 找到 RSS 条目: {len(entries)}")
            
            for entry in entries:
                try:
                    # 1. Title
                    title = entry.find('title').get_text(strip=True)
                    
                    # 2. ID/Link (Logic: User said link after "文章来源：" is the detail link)
                    # We look into summary for the source link first.
                    summary_html = ""
                    summary_tag = entry.find('summary')
                    if summary_tag:
                        summary_html = summary_tag.get_text() # CDATA or inner text
                        # If summary text contains HTML (which it does based on snippet), parse it
                        # The snippet shows <summary type="html">&lt;![CDATA[ ... ]]&gt;</summary> or parsed content
                        # BS4 xml parser should handle CDATA.
                    
                    # Parse summary HTML
                    summary_soup = BeautifulSoup(summary_html, 'html.parser')
                    
                    # Find source link
                    # User: "文章来源："后面的链接是文章的详细链接
                    # Snippet: <p><strong>文章来源：</strong></p><p><a href="...">...</a></p>
                    source_url = ""
                    article_source_label = summary_soup.find(string=re.compile("文章来源"))
                    if article_source_label:
                        # Find the next 'a' tag
                        # The label might be in a strong/p tag.
                        # Look for 'a' tag in the vicinity
                        parent = article_source_label.parent
                        # Go up to p and find next sibling p?
                        # Or just find the first 'a' tag after this string in the whole summary?
                        
                        # Let's try to find 'a' tag with href in the next sibling element 
                        # OR just search all 'a' tags and see which one is close.
                        # Simple robust way: Find all links, check if one looks like the source. 
                        # Specific logic: The snippet shows it's in a following <p>
                        
                        # Search for link in next paragraph
                        current = parent
                        while current:
                            current = current.next_sibling
                            if hasattr(current, 'find'):
                                found_link = current.find('a')
                                if found_link:
                                    source_url = found_link.get('href')
                                    break
                    
                    # Fallback to feed link if not found (though user said source link is key)
                    if not source_url:
                        link_tag = entry.find('link')
                        if link_tag:
                            source_url = link_tag.get('href')

                    # 3. Author
                    # <author><name>Vitalik Buterin</name></author>
                    author = "Chainfeeds"
                    author_tag = entry.find('author')
                    if author_tag and author_tag.find('name'):
                        author = author_tag.find('name').get_text(strip=True)

                    # 4. Date
                    # <updated>2025-12-31T07:08:19+00:00</updated>
                    published_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    updated_tag = entry.find('updated')
                    if updated_tag:
                        date_str = updated_tag.get_text(strip=True)
                        try:
                            # Parse ISO 8601
                            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            # Convert to Beijing (UTC+8)
                            dt_beijing = dt.astimezone(timezone(timedelta(hours=8)))
                            published_at = dt_beijing.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            print(f"  ⚠️ 时间解析失败: {e}")
                    
                    # 5. Content
                    # User: "Vitalik：..." content
                    # Extract pure text from summary, excluding "Chainfeeds 导读" header and "文章来源"
                    # Strategy: Get text from summary_soup, but remove known metadata lines
                    
                    # Remove "Chainfeeds 导读" section and links
                    for tag in summary_soup.find_all(['p', 'div']):
                        text = tag.get_text()
                        if "Chainfeeds 导读" in text or "文章来源" in text or "文章作者" in text or "内容来源" in text:
                            tag.decompose()
                    
                    # Remove all link tags to avoid URLs in content
                    for link in summary_soup.find_all('a'):
                        link.unwrap()  # Keep text, remove <a> tag
                            
                    content = summary_soup.get_text(strip=True, separator=' ')
                    
                    # Clean up extra whitespace
                    content = re.sub(r'\s+', ' ', content)
                    
                    # Limit content length to 500 characters
                    if len(content) > 500:
                        content = content[:500] + '...'
                    
                    # Check Incremental in Loop
                    if self.should_stop_scraping(title, source_url):
                        print(f"  [增量抓取] 停止: {title}")
                        break
                    
                    all_articles.append({
                        'title': title,
                        'content': content,
                        'url': source_url,
                        'published_at': published_at,
                        'source_site': self.site_name,
                        'author': author,
                        'type': self.news_type
                    })
                    print(f"  ✅ 抓取成功: {title} ({author})")
                
                except Exception as e:
                    print(f"  ⚠️ 处理单条失败: {e}")
                    continue
            
            # 限制数量
            if len(all_articles) > self.max_items:
                all_articles = all_articles[:self.max_items]

        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            import traceback
            traceback.print_exc()
        
        return all_articles

    async def _fetch_article_details(self, url: str) -> Optional[Dict]:
        return None
