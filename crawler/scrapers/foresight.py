"""Foresight News爬虫"""
from .base import BaseScraper
from typing import List, Dict
from datetime import datetime

class ForesightScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            site_name='foresight',
            base_url='https://foresightnews.pro/news'
        )
    
    async def scrape_important_news(self) -> List[Dict]:
        """抓取Foresight News的重要新闻"""
        await self.page.goto(self.base_url)
        await self.page.wait_for_timeout(3000)
        
        # 点击"只看重要"开关
        try:
            important_switch = await self.page.query_selector('text=只看重要')
            if important_switch:
                # 检查是否已开启
                is_active = await important_switch.get_attribute('class') # 假设class变化，这里需要具体分析HTML，但点击是toggle
                # Foresight的开关可能没有明确的aria-checked，简单起见先强制点击
                await self.page.evaluate("el => el.click()", important_switch)
                await self.page.wait_for_timeout(2000)
        except Exception as e:
            print(f"点击筛选按钮失败: {e}")
        
        news_list = []
        processed_urls = set()
        
        # 先获取当前页面的日期标题（如"12月24日"）
        date_headers = await self.page.query_selector_all('.collapse-title-month')
        current_date_str = None
        if date_headers:
            # 通常第一个就是最新的日期
            current_date_str = await self.safe_extract_text(date_headers[0])
            print(f"[DEBUG] 当前日期区块: {current_date_str}")
        
        # 获取所有新闻标题
        title_elements = await self.page.query_selector_all('.news_body_title')
        print(f"[DEBUG] 找到 {len(title_elements)} 个新闻标题")
        
        for title_el in title_elements:
            try:
                # 检查是否有redcolor类
                class_name = await title_el.get_attribute('class')
                has_red_class = 'redcolor' in class_name if class_name else False
                
                # 样式检查（通用方法）
                style_check = await self.check_importance_by_style(title_el)
                
                # 只要满足任一条件即为重要
                if not (has_red_class or style_check['is_important']):
                    continue
                
                # 提取信息
                title = await self.safe_extract_text(title_el)
                url = await self.safe_get_attribute(title_el, 'href')
                
                if url and not url.startswith('http'):
                    # Remove /foresightnews prefix if present, then add base URL
                    if url.startswith('/foresightnews/'):
                        url = f"https://foresightnews.pro{url[len('/foresightnews'):]}"
                    else:
                        url = f"https://foresightnews.pro{url}"
                
                if url in processed_urls:
                    continue
                processed_urls.add(url)
                
                # 提取时间：查找最近的时间戳元素
                published_at = None
                try:
                    # 向上找父容器，然后找时间戳
                    time_element = await title_el.evaluate('''
                        el => {
                            // 向上找到包含时间戳的容器
                            let parent = el.closest('.el-timeline-item') || el.closest('div');
                            if (parent) {
                                let timeEl = parent.querySelector('.el-timeline-item__timestamp.is-top');
                                return timeEl ? timeEl.textContent.trim() : '';
                            }
                            return '';
                        }
                    ''')
                    
                    if time_element and current_date_str:
                        # 解析日期和时间，组合成完整的datetime
                        # current_date_str 格式: "12月24日"
                        # time_element 格式: "19:56"
                        import re
                        date_match = re.search(r'(\d+)月(\d+)日', current_date_str)
                        time_match = re.search(r'(\d+):(\d+)', time_element)
                        
                        if date_match and time_match:
                            month = int(date_match.group(1))
                            day = int(date_match.group(2))
                            hour = int(time_match.group(1))
                            minute = int(time_match.group(2))
                            
                            now = datetime.now()
                            published_at = now.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)
                except Exception as e:
                    print(f"  时间提取失败: {e}")
                
                # 如果时间提取失败，使用当前时间
                if published_at is None:
                    published_at = datetime.now()
                
                # 确定重要标识
                if has_red_class:
                    importance_flag = 'redcolor_class'
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
                    try:
                        # 直接打开详情页
                        detail_page = await self.context.new_page()
                        await detail_page.goto(url, wait_until='domcontentloaded')
                        await detail_page.wait_for_timeout(2000)
                        
                        # 使用inner_text()获取纯文本
                        content_el = await detail_page.query_selector('.detail-body')
                        if content_el:
                            content = await content_el.inner_text()
                        
                        # 清理内容
                        content = self.clean_content(content, title)
                        
                        await detail_page.close()
                    except Exception as e:
                        print(f"  获取详细内容失败: {e}")
                
                # 如果没获取到内容，使用标题作为fallback
                if not content or len(content) < 10:
                    content = title
                
                news_item = {
                    'title': title,
                    'content': content,
                    'url': url,
                    'source_site': self.site_name,
                    'published_at': published_at,
                    'is_marked_important': True,
                    'site_importance_flag': importance_flag
                }
                
                news_list.append(news_item)
                print(f"[DEBUG] 添加重要新闻: {title[:30]}...")
                
            except Exception as e:
                print(f"解析Foresight新闻项失败: {e}")
                continue
        
        print(f"Foresight News: 抓取到 {len(news_list)} 条重要新闻")
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


# 测试代码
if __name__ == '__main__':
    import asyncio
    
    async def test():
        scraper = ForesightScraper()
        news = await scraper.run()
        
        for item in news[:3]:
            print(f"\n标题: {item['title']}")
            print(f"链接: {item['url']}")
            print(f"标识: {item['site_importance_flag']}")
    
    asyncio.run(test())
