from __future__ import annotations

from datetime import datetime
from email.utils import format_datetime
from html import escape
from typing import Dict, Optional

from ..infrastructure.repositories import repositories


class PublicContentService:
    @staticmethod
    def _repos():
        return repositories()

    def get_public_content(self, content_kind: str, limit: int, offset: int) -> Dict:
        return self._repos().review_public.list_public_entries(content_kind, limit, offset)

    def get_public_reports(self, content_kind: Optional[str], limit: int, offset: int) -> Dict:
        return self._repos().daily_reports.list_reports(content_kind, limit, offset)

    def search_public_content(self, query_text: str, content_kind: str, limit: int, offset: int) -> Dict:
        return self._repos().review_public.search_public_entries(query_text, content_kind, limit, offset)

    def build_public_rss(self, content_kind: str, limit: int) -> str:
        payload = self.get_public_content(content_kind, limit, 0)
        items = payload.get("items", [])
        title = "AINews 快讯" if content_kind == "news" else "AINews 文章"
        description = "AINews 公开内容 RSS"
        pub_date = format_datetime(datetime.now())
        xml_items = "\n".join(self._rss_item_xml(item) for item in items)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0">\n'
            "  <channel>\n"
            f"    <title>{escape(title)}</title>\n"
            "    <link>https://ainews.local/</link>\n"
            f"    <description>{escape(description)}</description>\n"
            "    <language>zh-cn</language>\n"
            f"    <lastBuildDate>{pub_date}</lastBuildDate>\n"
            f"{xml_items}\n"
            "  </channel>\n"
            "</rss>\n"
        )

    def _rss_item_xml(self, item: Dict) -> str:
        link = item.get("source_url") or ""
        description = item.get("review_summary") or item.get("review_reason") or ""
        pub_date = self._rss_pub_date(item.get("published_at"))
        return (
            "    <item>\n"
            f"      <title>{escape(item.get('title') or '')}</title>\n"
            f"      <link>{escape(link)}</link>\n"
            f"      <guid>{escape(link or str(item.get('id') or ''))}</guid>\n"
            f"      <description>{escape(description)}</description>\n"
            f"      <category>{escape(item.get('review_category') or item.get('source_site') or '')}</category>\n"
            f"      <pubDate>{pub_date}</pubDate>\n"
            "    </item>"
        )

    @staticmethod
    def _rss_pub_date(value: str | None) -> str:
        if not value:
            return format_datetime(datetime.now())
        for parser in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return format_datetime(datetime.strptime(value, parser))
            except Exception:
                continue
        return format_datetime(datetime.now())


public_content_service = PublicContentService()
