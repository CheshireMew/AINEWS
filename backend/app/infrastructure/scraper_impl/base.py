"""爬虫基类。"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

from playwright.async_api import Browser, Page

from .browser_runtime import close_browser, fetch_page_with_delay, init_browser
from .content_tools import (
    check_importance_by_style,
    clean_content,
    fetch_full_content,
    parse_relative_time,
    safe_extract_text,
    safe_get_attribute,
)
from .incremental_state import load_last_news, should_stop_scraping


class BaseScraper(ABC):
    """所有爬虫的基类。"""

    def __init__(self, site_name: str, base_url: str, max_items: int = 10):
        self.site_name = site_name
        self.base_url = base_url
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.last_news_title = None
        self.last_news_url = None
        self.existing_urls = set()
        self.last_news_time = None
        self.incremental_mode = True
        self.max_items = max_items

    async def init_browser(self, headless: bool = True):
        await init_browser(self, headless)

    async def close_browser(self):
        await close_browser(self)

    async def fetch_page_with_delay(
        self,
        url: str,
        delay_range: tuple = (1, 3),
        max_retries: int = 3,
        return_response: bool = False,
        page: Optional[Page] = None,
    ):
        return await fetch_page_with_delay(self, url, delay_range, max_retries, return_response, page)

    @abstractmethod
    async def scrape_important_news(self) -> List[Dict]:
        pass

    async def click_important_filter(self, selector: str):
        try:
            await self.page.click(selector)
            await self.page.wait_for_timeout(2000)
        except Exception as exc:
            print(f"点击筛选器失败: {exc}")

    def generate_url_hash(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    async def safe_extract_text(self, element, selector: str = None) -> str:
        return await safe_extract_text(element, selector)

    async def safe_get_attribute(self, element, attr: str) -> str:
        return await safe_get_attribute(element, attr)

    def clean_content(self, content: str, title: str = "") -> str:
        return clean_content(content, title)

    def parse_relative_time(self, time_str: str) -> Optional[datetime]:
        return parse_relative_time(time_str)

    async def check_importance_by_style(self, element) -> Dict:
        return await check_importance_by_style(element)

    async def fetch_full_content(self, detail_url: str, content_selectors: List[str] = None, extract_paragraphs: bool = False) -> str:
        return await fetch_full_content(self, detail_url, content_selectors, extract_paragraphs)

    def load_last_news(self, db):
        load_last_news(self, db)

    def should_stop_scraping(self, news_title: str, news_url: str, news_time: datetime = None) -> bool:
        return should_stop_scraping(self, news_title, news_url, news_time)

    async def run(self) -> List[Dict]:
        try:
            await self.init_browser()
            return await self.scrape_important_news()
        except Exception as exc:
            print(f"{self.site_name}爬虫错误: {exc}")
            return []
        finally:
            await self.close_browser()
