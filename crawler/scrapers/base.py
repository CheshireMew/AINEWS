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
        """初始化Playwright浏览器（增强反检测）"""
        import random
        
        self.playwright = await async_playwright().start()
        
        # 启动参数 - 禁用自动化检测特征
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',  # 关键：禁用自动化标志
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-infobars',
            ]
        )
        
        self.page = await self.browser.new_page()
        
        # 1. 注入脚本：覆盖 navigator.webdriver
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # 2. 设置随机视口大小（模拟真实用户的不同屏幕）
        viewport_options = [
            {"width": 1920, "height": 1080},  # Full HD
            {"width": 1366, "height": 768},   # 常见笔记本
            {"width": 1536, "height": 864},   # 常见笔记本
            {"width": 1440, "height": 900},   # MacBook
            {"width": 2560, "height": 1440},  # 2K
        ]
        viewport = random.choice(viewport_options)
        await self.page.set_viewport_size(viewport)
        
        # 3. 设置超时
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
    
    async def fetch_page_with_delay(self, url: str, delay_range: tuple = (1, 3), max_retries: int = 3, return_response: bool = False, page: Optional[Page] = None):
        """
        带延迟和重试的页面访问（反爬策略）
        
        Args:
            url: 要访问的URL
            delay_range: 延迟时间范围（秒），如(1, 3)表示1-3秒随机延迟
            max_retries: 最大重试次数
            return_response: 是否返回Response对象而不是Page对象
            page: 指定使用的Page对象，若为None则使用self.page
            
        Returns:
            Page对象 或 Response对象
        
        Raises:
            Exception: 重试失败后抛出异常
        """
        import random
        import sys
        sys.path.insert(0, 'E:/Work/Code/AINEWS/backend')
        from utils.user_agents import get_random_user_agent
        
        target_page = page if page else self.page
        
        # 请求前延迟（使用正态分布生成更自然的延迟）
        mean_delay = sum(delay_range) / 2
        std_delay = (delay_range[1] - delay_range[0]) / 4
        delay = max(delay_range[0], min(delay_range[1], random.gauss(mean_delay, std_delay)))
        await asyncio.sleep(delay)
        
        # 重试逻辑  
        for attempt in range(max_retries):
            try:
                # 设置随机User-Agent
                user_agent = get_random_user_agent()
                
                # 生成完整的请求头（模拟真实浏览器）
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                }
                
                # 如果是 Chrome 浏览器，添加 sec-ch-ua 系列头
                if 'Chrome' in user_agent and 'Edg' not in user_agent:
                    # 从 UA 提取版本号
                    import re
                    match = re.search(r'Chrome/(\d+)', user_agent)
                    chrome_version = match.group(1) if match else '131'
                    
                    headers['sec-ch-ua'] = f'"Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}", "Not?A_Brand";v="99"'
                    headers['sec-ch-ua-mobile'] = '?0'
                    headers['sec-ch-ua-platform'] = '"Windows"' if 'Windows' in user_agent else ('"macOS"' if 'Mac' in user_agent else '"Linux"')
                
                await target_page.set_extra_http_headers(headers)
                
                # 访问页面
                response = await target_page.goto(url, wait_until='domcontentloaded')
                
                if return_response:
                    return response
                    
                return target_page
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # 指数退避（增加随机性）
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    print(f"[反爬] 请求失败，{wait_time:.1f}秒后重试 (attempt {attempt + 1}/{max_retries}): {str(e)[:50]}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"[反爬] 请求最终失败 ({max_retries}次重试后): {url}")
                    raise
    
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
    
    
    def clean_content(self, content: str, title: str = "") -> str:
        """
        清理新闻内容，去除固定前缀和重复标题
        """
        import re
        
        if not content:
            return content
        
        # 0. 预处理：首尾去空
        content = content.strip()
        
        # 1. 去除 marsbit 的【标题】格式
        content = re.sub(r'^【[^】]+】', '', content).strip()
        
        # 2. 去除各网站的固定前缀
        prefixes = [
            r'^Odaily(?:星球日报)?\s*(?:讯|消息|报道)[\s，,]*',
            r'^PANews(?:\s+\d+月\d+日)?\s*(?:讯|消息|报道)[\s，,]*',
            r'^ChainCatcher\s*(?:讯|消息|报道)[\s，,]*',
            r'^BlockBeats\s*(?:讯|消息|报道)[\s，,]*',
            r'^深潮\s*(?:TechFlow)?\s*(?:讯|消息|报道)[\s，,]*',
            r'^Foresight(?:\s*News)?\s*(?:讯|消息|报道|快讯)[\s，,]*',
            r'^火星财经\s*(?:讯|消息|报道)[\s，,]*',
            r'^MarsBit\s*(?:讯|消息|报道)[\s，,]*',
            r'^[\s，,]*消息[\s，,]*',
        ]
        
        original_len = len(content)
        for prefix_pattern in prefixes:
            content = re.sub(prefix_pattern, '', content, count=1, flags=re.IGNORECASE).strip()
        
        if len(content) < original_len:
            # print(f"  [DEBUG] Cleared prefix, length delta: {original_len - len(content)}")
            pass
            
        # 3. 如果提供了标题，且内容开头包含标题，则去除
        if title and content.startswith(title):
            remaining = content[len(title):].strip()
            # 只在以下情况删除标题：
            # 1. 标题后有明确的分隔符（换行、句号、问号、感叹号）
            # 2. 或者剩余内容足够长（至少50个字符）且以标点开头
            if remaining:
                # 检查是否以常见分隔符开头
                if remaining[0] in '。？！\n\r，,：:':
                    # 去除可能跟随的标点符号和空格
                    content = re.sub(r'^[，,：:、。？！\s]+', '', remaining)
                elif len(remaining) > 50 and not remaining[0].isalnum():
                    # 剩余内容较长且以非字母数字开头（如标点），可能是分隔
                    content = re.sub(r'^[，,：:、\s]+', '', remaining)
        
        return content.strip()
    
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
            dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            # 如果时间在未来，说明是昨天
            if dt > now:
                dt -= timedelta(days=1)
            return dt
        
        # 匹配"MM月DD日 HH:MM"
        match = re.search(r'(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{2})', time_str)
        if match:
            month, day, hour, minute = map(int, match.groups())
            # 使用datetime构造，避免replace跨月问题
            try:
                dt = datetime(now.year, month, day, hour, minute, 0)
            except ValueError:
                # 日期无效，使用当前时间
                return now
            else:
                # 如果时间在未来（跨年情况），使用去年
                if dt > now:
                    dt = dt.replace(year=now.year - 1)
                return dt

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
    
    async def fetch_full_content(self, detail_url: str, content_selectors: List[str] = None, extract_paragraphs: bool = False) -> str:
        """
        访问新闻详情页，获取完整内容（通用方法）
        Args:
            detail_url: 详情页URL
            content_selectors: 内容区域选择器列表
            extract_paragraphs: 是否遍历提取 <p> 标签内容并合并 (适用于 Foresight/PANews 等)
        """
        if not content_selectors:
            content_selectors = [
                '.article-content',
                '.art_detail_content', # TechFlow
                '.rich_text_content', # ChainCatcher
                '.flash-content', # BlockBeats/MarsBit
                '.detail-body', # Foresight
                '.news_body_content',
                'article.prose', # PANews
                'article',
                '.content',
            ]
        
        try:
            print(f"  [DEBUG] Fetching content from: {detail_url}")
            detail_page = await self.browser.new_page()
            
            # 使用 domcontentloaded 等待，配合重试机制处理SPA动态加载，避免死等 networkidle
            try:
                await detail_page.goto(detail_url, wait_until='domcontentloaded', timeout=30000)
            except Exception as e:
                print(f"  [DEBUG] Navigation timeout (continuing): {e}")

            full_content = ""
            
            # 增加重试机制 (最多尝试5次，每次间隔1.5秒)
            for attempt in range(5):
                try:
                    for selector in content_selectors:
                        try:
                            content_el = await detail_page.query_selector(selector)
                            if content_el:
                                if extract_paragraphs:
                                    # 提取所有 p 和 li 标签
                                    elements = await content_el.query_selector_all('p, li')
                                    if elements:
                                        lines = []
                                        for el in elements:
                                            text = await self.safe_extract_text(el)
                                            if text:
                                                # 如果是列表项，加个前缀
                                                tag_name = await el.evaluate('el => el.tagName')
                                                if tag_name == 'LI':
                                                    text = f"- {text}"
                                                lines.append(text)
                                        full_content = '\n\n'.join(lines)
                                    else:
                                        # 如果没有 p 标签，回退到 inner_text
                                        full_content = await self.safe_extract_text(content_el)
                                else:
                                    # 标准模式：直接获取 inner_text
                                    full_content = await self.safe_extract_text(content_el)
                                
                                if full_content and len(full_content) > 20: # 内容检查
                                    break
                        except:
                            continue
                    
                    if full_content and len(full_content) > 20:
                        break # 成功获取
                        
                    # 等待加载
                    await detail_page.wait_for_timeout(1500)
                    
                except Exception as e:
                    print(f"  [Attempt {attempt+1}] 获取内容尝试失败: {e}")
            
            # 失败调试
            if not full_content:
                print(f"  [WARNING] 无法获取内容: {detail_url}")
                try:
                    body = await detail_page.inner_html('body')
                    print(f"  [DEBUG] Body Preview: {body[:200]}...")
                except: pass
            
            await detail_page.close()
            return full_content if full_content else ""
            
        except Exception as e:
            print(f"  获取详情页失败: {e}")
            return ""
    
    def load_last_news(self, db):
        """
        从数据库加载最新新闻信息（用于增量抓取）
        + 加载最近批量URL用于多专栏/乱序抓取的去重
        """
        self.db = db  # 保存 DB 引用供子类使用
        
        if not self.incremental_mode:
            return
            
        try:
             # 直接查询数据库获取最近的一批记录（200条），以支持多专栏并行抓取时的去重
             conn = db.connect()
             cursor = conn.cursor()
             
             cursor.execute('''
                SELECT source_url, title, published_at FROM news 
                WHERE source_site = ? 
                ORDER BY published_at DESC 
                LIMIT 200
             ''', (self.site_name,))
             
             rows = cursor.fetchall()
             try:
                 conn.close()
             except: pass
             
             if rows:
                 # 1. 设置最新一条的状态（作为主要参考）
                 latest = rows[0] # tuple: (url, title, published_at)
                 self.last_news_url = latest[0]
                 self.last_news_title = latest[1]
                 
                 # 处理时间
                 t = latest[2]
                 self.last_news_time = None
                 if t:
                     if isinstance(t, str):
                         try:
                            # 尝试常用格式
                            self.last_news_time = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
                         except:
                            try:
                                self.last_news_time = datetime.fromisoformat(t)
                            except: pass
                     elif isinstance(t, datetime):
                         self.last_news_time = t
                     
                 # 2. 填充 existing_urls 集合（用于更健壮的去重）
                 count = 0
                 for row in rows:
                     url = row[0]
                     if url:
                         self.existing_urls.add(url)
                         count += 1
                 
                 print(f"[增量抓取] {self.site_name}: 已加载 {count} 条历史URL用于去重")
                 print(f"[增量抓取] 最新记录: {self.last_news_title[:30]}... ({self.last_news_time})")
             else:
                 print(f"[增量抓取] {self.site_name}: 未找到历史记录，将全量抓取")
                 self.last_news_title = None
                 self.last_news_url = None
                 self.last_news_time = None
                 
        except Exception as e:
            print(f"[增量抓取] 加载历史记录失败: {e}")
            # 出错时不停止，降级为全量抓取
    
    
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
