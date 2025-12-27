"""深潮TechFlow爬虫"""
from .base import BaseScraper
from typing import List, Dict
from datetime import datetime

class TechFlowScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name='techflow',
            base_url='https://www.techflowpost.com/newsletter/index.html'
        )
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取深潮的重要新闻"""
        await self.fetch_page_with_delay(self.base_url)
        
        # 点击"只看精选"
        try:
            # 找到"只看精选"按钮并点击
            filter_btn = await self.page.query_selector('.chose')
            if filter_btn:
                # 检查是否已激活
                class_name = await filter_btn.get_attribute('class')
                if 'crently' not in class_name:
                    await self.page.evaluate("el => el.click()", filter_btn)
                    await self.page.wait_for_timeout(2000)
        except Exception as e:
            print(f"点击筛选按钮失败: {e}")
        
        news_list = []
        processed_urls = set()
        
        # 获取所有新闻项
        dl_elements = await self.page.query_selector_all('dl')
        print(f"[DEBUG] 找到 {len(dl_elements)} 个dl元素")
        
        for dl in dl_elements:
            try:
                # 获取时间（dt元素）
                dt = await dl.query_selector('dt')
                if not dt:
                    continue
                
                time_text = await self.safe_extract_text(dt)
                
                # 获取新闻内容（dd元素）
                dd = await dl.query_selector('dd')
                if not dd:
                    continue
                
                #获取标题链接
                title_link = await dd.query_selector('a.dfont.f18')
                if not title_link:
                    continue
                
                # 检查是否有重要标识
                class_name = await title_link.get_attribute('class')
                has_important_class = 'c002CCC' in class_name
                
                # 检查是否有"首发"图标
                first_pub_icon = await title_link.query_selector('img[src*="first_pub_ico"]')
                has_first_pub = first_pub_icon is not None
                
                # 只有标记为重要的才添加
                if not (has_important_class or has_first_pub):
                    continue
                
                title = await self.safe_extract_text(title_link)
                url = await self.safe_get_attribute(title_link, 'href')
                
                # 补全URL
                if url and not url.startswith('http'):
                    url = f"https://www.techflowpost.com{url}"
                
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                
                # 解析时间
                published_at = self.parse_relative_time(time_text) if time_text else datetime.now()

                # 增量抓取：检查是否已经抓到上次的新闻
                if self.should_stop_scraping(title, url, published_at):
                    break  # 停止抓取
                
                # 数量限制：检查是否已达到最大抓取数量
                if len(news_list) >= self.max_items:
                    print(f"[数量限制] 已达到最大抓取数量 {self.max_items}，停止抓取")
                    break
                
                # 获取快讯摘要作为fallback
                content_div = await dd.query_selector('.f12.line18')
                summary = await self.safe_extract_text(content_div) if content_div else ""
                

                
                # 访问详情页获取完整内容（使用正确的选择器）
                full_content = await self.fetch_full_content(
                    url, 
                    content_selectors=['.art_detail_content']  # TechFlow特定选择器
                ) if url else ""
                
                # 清理内容前缀
                full_content = self.clean_content(full_content, title)
                
                # 如果没获取到内容，使用摘要
                if not full_content or len(full_content) < 50:
                    full_content = summary
                
                news_item = {
                    'title': title,
                    'content': full_content,
                    'url': url,
                    'published_at': published_at,
                    'is_marked_important': True,
                    'site_importance_flag': 'c002CCC' if has_important_class else 'first_pub'
                }
                
                news_list.append(news_item)
                print(f"[DEBUG] 添加重要新闻: {title[:30]}...")
                
            except Exception as e:
                print(f"[DEBUG] 解析新闻项失败: {e}")
                continue
        
        print(f"深潮TechFlow: 抓取到 {len(news_list)} 条重要新闻")
        return news_list



# 测试代码
if __name__ == '__main__':
    import asyncio
    
    async def test():
        scraper = TechFlowScraper()
        news = await scraper.run()
        
        for item in news[:5]:
            print(f"\n标题: {item['title']}")
            print(f"链接: {item['url']}")
            print(f"时间: {item['published_at']}")
            print(f"标识: {item['site_importance_flag']}")
    
    asyncio.run(test())
