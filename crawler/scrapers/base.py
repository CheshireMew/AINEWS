"""爬虫基类"""
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime
import hashlib
from typing import List, Dict, Optional
import asyncio

class BaseScraper(ABC):
    """所有爬虫的基类"""
    
    def __init__(self, site_name: str, base_url: str, max_items: int = 10):
        self.site_name = site_name
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # 增量抓取相关
        self.last_news_title = None  # 上次最新新闻的标题
        self.last_news_url = None     # 上次最新新闻的URL
        self.existing_urls = set()    # 最近已抓取的URL集合（用于更健壮的去重）
        self.last_news_time = None    # 上次最新新闻的时间
        self.incremental_mode = True   # 是否启用增量抓取（默认启用）
        
        # 数量限制
        self.max_items = max_items  # 每次抓取的最大新闻数量
    
    async def init_browser(self, headless: bool = True):
        """初始化Playwright浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()
        
        # 设置超时
        self.page.set_default_timeout(30000)
        self.page.set_default_navigation_timeout(30000)
    
    async def close_browser(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    @abstractmethod
    async def scrape_important_news(self) -> List[Dict]:
        """
        抓取重要新闻（子类必须实现）
        
        返回格式：
        [{
            'title': '新闻标题',
            'content': '新闻内容（可选）',
            'url': '原文链接',
            'published_at': datetime对象,
            'is_marked_important': True,
            'site_importance_flag': '网站的重要标识'
        }]
        """
        pass
    
    async def click_important_filter(self, selector: str):
        """点击"只看重要"开关"""
        try:
            await self.page.click(selector)
            await self.page.wait_for_timeout(2000)  # 等待加载
        except Exception as e:
            print(f"点击筛选器失败: {e}")
    
    def generate_url_hash(self, url: str) -> str:
        """生成URL的hash用于去重"""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def safe_extract_text(self, element, selector: str = None) -> str:
        """安全提取文本"""
        try:
            if selector:
                target = await element.query_selector(selector)
                if target:
                    return (await target.inner_text()).strip()
            else:
                return (await element.inner_text()).strip()
        except:
            return ""
        return ""
    
    async def safe_get_attribute(self, element, attr: str) -> str:
        """安全获取属性"""
        try:
            value = await element.get_attribute(attr)
            return value if value else ""
        except:
            return ""
    
    def parse_relative_time(self, time_str: str) -> Optional[datetime]:
        """
        解析相对时间（如"2小时前"）为datetime对象
        """
        import re
        from datetime import timedelta
        
        now = datetime.now()
        
        # 匹配"X分钟前"
        match = re.search(r'(\d+)\s*分钟', time_str)
        if match:
            minutes = int(match.group(1))
            return now - timedelta(minutes=minutes)
        
        # 匹配"X小时前"
        match = re.search(r'(\d+)\s*小时', time_str)
        if match:
            hours = int(match.group(1))
            return now - timedelta(hours=hours)
        
        # 匹配"今天 HH:MM"
        match = re.search(r'今天\s+(\d{1,2}):(\d{2})', time_str)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 匹配"MM月DD日 HH:MM"
        match = re.search(r'(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{2})', time_str)
        if match:
            month, day, hour, minute = map(int, match.groups())
            return now.replace(month=month, day=day, hour=hour, minute=minute, second=0, microsecond=0)

        # 匹配纯 "HH:MM" (假设是今天)
        match = re.search(r'^(\d{1,2}):(\d{2})$', time_str.strip())
        if match:
            hour, minute = map(int, match.groups())
            dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if dt > now:
                dt -= timedelta(days=1)
            return dt
        
        return None
    
    async def check_importance_by_style(self, element) -> Dict:
        """
        通过CSS样式判断元素是否重要
        检查：颜色（红色/特殊色）、字体粗细（bold）、字体大小
        
        返回: {
            'is_important': bool,
            'reasons': list,  # 判断依据
            'style_flag': str  # 样式标识
        }
        """
        try:
            style_info = await element.evaluate('''
                el => {
                    const computed = window.getComputedStyle(el);
                    return {
                        color: computed.color,
                        fontWeight: computed.fontWeight,
                        fontSize: computed.fontSize,
                        backgroundColor: computed.backgroundColor
                    };
                }
            ''')
            
            reasons = []
            
            # 解析颜色（检查是否是红色系或特殊色）
            color = style_info.get('color', '')
            if color:
                # RGB色值检查（红色系）
                import re
                rgb_match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                if rgb_match:
                    r, g, b = map(int, rgb_match.groups())
                    # 红色为主（r > 200 且 r > g+50 且 r > b+50）
                    if r > 200 and r > g + 50 and r > b + 50:
                        reasons.append('red_color')
                    # 橙色/金色
                    elif r > 200 and g > 100 and b < 100:
                        reasons.append('orange_color')
            
            # 检查字体粗细
            font_weight = style_info.get('fontWeight', '')
            if font_weight:
                # bold 或 数值 >= 600
                if font_weight == 'bold' or (font_weight.isdigit() and int(font_weight) >= 600):
                    reasons.append('bold_font')
            
            # 检查字体大小（如果明显大于常规）
            font_size = style_info.get('fontSize', '')
            if font_size and 'px' in font_size:
                size = int(font_size.replace('px', ''))
                if size >= 18:  # 大于等于18px视为重要
                    reasons.append('large_font')
            
            is_important = len(reasons) > 0
            style_flag = '+'.join(reasons) if reasons else 'normal'
            
            return {
                'is_important': is_important,
                'reasons': reasons,
                'style_flag': style_flag
            }
            
        except Exception as e:
            print(f"检查样式失败: {e}")
            return {
                'is_important': False,
                'reasons': [],
                'style_flag': 'unknown'
            }
    
    async def fetch_full_content(self, detail_url: str, content_selectors: List[str] = None) -> str:
        """
        访问新闻详情页，获取完整内容（通用方法）
        子类可以传入自定义的选择器列表
        """
        if not content_selectors:
            content_selectors = [
                '.article-content',
                '.aritcle_content',
                '.content',
                'article',
                '.detail-content',
                '.news-content',
                '.post-content',
                '.entry-content'
            ]
        
        try:
            detail_page = await self.browser.new_page()
            await detail_page.goto(detail_url, timeout=15000)
            await detail_page.wait_for_timeout(1500)
            
            full_content = ""
            for selector in content_selectors:
                content_el = await detail_page.query_selector(selector)
                if content_el:
                    full_content = await self.safe_extract_text(content_el)
                    if full_content and len(full_content) > 50:
                        break
            
            await detail_page.close()
            return full_content if full_content else ""
            
        except Exception as e:
            print(f"  获取详情页失败: {e}")
            return ""
    
    def load_last_news(self, db):
        """
        从数据库加载最新新闻信息（用于增量抓取）
        
        Args:
            db: Database实例
        """
        if not self.incremental_mode:
            return
        
        latest = db.get_latest_news(self.site_name)
        if latest:
            self.last_news_title = latest['title']
            self.last_news_url = latest['source_url']
            
            # Load time if available
            self.last_news_time = None
            if 'published_at' in latest and latest['published_at']:
                # Ensure it's datetime object. Sqlite adapter might return str
                t = latest['published_at']
                if isinstance(t, str):
                    try:
                        self.last_news_time = datetime.fromisoformat(t)
                    except:
                        pass # Keep None
                elif isinstance(t, datetime):
                    self.last_news_time = t
                    
            print(f"[增量抓取] 上次最新: {self.last_news_title[:30]}... ({self.last_news_time})")
        else:
            print(f"[增量抓取] 未找到历史记录，将抓取所有新闻")
            self.last_news_title = None
            self.last_news_url = None
            self.last_news_time = None
    
    
    def should_stop_scraping(self, news_title: str, news_url: str, news_time: datetime = None) -> bool:
        """
        判断是否应该停止抓取（已经抓到上次的新闻）
        
        Args:
            news_title: 当前新闻标题
            news_url: 当前新闻URL
            news_time: 当前新闻发布时间 (Optional)
            
        Returns:
            True表示应该停止，False表示继续
        """
        if not self.incremental_mode:
            return False
        
        # 如果没有任何历史记录，继续抓取
        if not self.last_news_title and not self.last_news_url:
            return False
        
        stop = False
        
        # 1. 通过标题匹配（去除空格后比较）
        if self.last_news_title:
            if news_title.replace(' ', '') == self.last_news_title.replace(' ', ''):
                print(f"[增量抓取] 匹配到上次新闻（标题），停止抓取")
                stop = True
        
        # 2. 通过URL匹配
        if not stop:
            # 优先检查集合（更健壮）
            if news_url in self.existing_urls:
                print(f"[增量抓取] 匹配到历史记录（URL集合），停止抓取")
                stop = True
            
            # 兼容旧逻辑
            elif self.last_news_url and news_url == self.last_news_url:
                print(f"[增量抓取] 匹配到上次新闻（URL），停止抓取")
                stop = True
                
        # 3. 通过时间匹配 (User Request)
        # 只有当明确传入了 news_time 且我们有 last_news_time 时才比较
        if not stop and news_time and self.last_news_time:
            # 比较时间戳，允许微小误差吗？用户说 "last three have one matching"
            # 通常 published_at 在数据库是 datetime
            if news_time == self.last_news_time:
                print(f"[增量抓取] 匹配到上次新闻（时间），停止抓取")
                stop = True
                
        return stop
    
    async def run(self) -> List[Dict]:
        """运行爬虫（完整流程）"""
        try:
            await self.init_browser()
            news_list = await self.scrape_important_news()
            return news_list
        except Exception as e:
            print(f"{self.site_name}爬虫错误: {e}")
            return []
        finally:
            await self.close_browser()
