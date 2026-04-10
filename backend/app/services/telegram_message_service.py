from __future__ import annotations

import html as html_lib
from typing import Dict, List

from shared.content_contract import CONTENT_KIND_ARTICLE, CONTENT_KIND_NEWS


class TelegramMessageService:
    @staticmethod
    def format_entry(entry: Dict) -> str:
        escaped_title = html_lib.escape(entry["title"])
        if (entry.get("content_type") or CONTENT_KIND_NEWS) == CONTENT_KIND_ARTICLE:
            return f'📰 <b><a href="{entry["source_url"]}">{escaped_title}</a></b>'
        return f'⚡ <b><a href="{entry["source_url"]}">{escaped_title}</a></b>\n\n{html_lib.escape(entry.get("content") or "")}'

    def build_daily_report(self, entries: List[Dict], content_kind: str, now) -> tuple[str, List[str]]:
        formatted_items = []
        seen_identifiers = set()
        for entry in entries:
            identifier = entry.get("source_url") or entry["title"]
            if identifier in seen_identifiers:
                continue
            seen_identifiers.add(identifier)
            formatted_items.append(f'<a href="{entry["source_url"]}">{html_lib.escape(entry["title"])}</a>')

        report_title = f"{now.strftime('%Y-%m-%d')} {'深度日报' if content_kind == CONTENT_KIND_ARTICLE else '精选日报'}"
        return report_title, formatted_items

    @staticmethod
    def compose_daily_report_part(report_title: str, items: List[str]) -> str:
        return (
            f"📅 <b>{report_title}</b>\n\n"
            + "\n\n".join(items)
            + "\n\n🤖 由 <a href=\"https://t.me/CheshireBTC\">AINEWS</a> 自动生成"
        )

    def split_daily_report_parts(self, report_title: str, items: List[str], limit: int = 4096) -> List[str]:
        if not items:
            return [self.compose_daily_report_part(report_title, [])]

        parts: List[str] = []
        current_items: List[str] = []
        for item in items:
            candidate_items = [*current_items, item]
            candidate_text = self.compose_daily_report_part(report_title, candidate_items)
            if current_items and len(candidate_text) > limit:
                parts.append(self.compose_daily_report_part(report_title, current_items))
                current_items = [item]
            else:
                current_items = candidate_items

        if current_items:
            parts.append(self.compose_daily_report_part(report_title, current_items))
        return parts


telegram_message_service = TelegramMessageService()
