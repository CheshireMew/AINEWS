
from .base import BaseScraper
from typing import List, Dict

class ArticleScraper(BaseScraper):
    """
    文章类爬虫基类
    用于抓取深度文章（非快讯），默认 type='article'
    """
    
    def __init__(self, site_name: str, base_url: str, max_items: int = 10):
        super().__init__(site_name, base_url, max_items)
        self.news_type = 'article'  # 核心区别：内容类型为 article

    async def scrape_important_news(self) -> List[Dict]:
        """
        子类实现具体的抓取逻辑
        注意：返回的字典中必须包含 'type': self.news_type
        """
        raise NotImplementedError
