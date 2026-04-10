from __future__ import annotations

import re
from typing import Dict, Optional

from shared.content_contract import ARCHIVED_STAGE, DUPLICATE_STAGE, INCOMING_STAGE
from .base_repository import BaseRepository
from .time_utils import get_beijing_time


class NewsRepository(BaseRepository):
    @staticmethod
    def _normalize_news_content(content: str) -> str:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return re.sub(r"\n\s*\n+", "\n", normalized).strip()

    def insert_news(self, news_data: Dict) -> Optional[int]:
        try:
            if news_data.get("content"):
                news_data["content"] = self._normalize_news_content(news_data["content"])

            scraped_at = get_beijing_time().strftime("%Y-%m-%d %H:%M:%S")
            cursor = self.execute(
                """
                INSERT INTO news (
                    title, content, source_site, source_url, published_at, scraped_at,
                    is_marked_important, site_importance_flag, stage, type, author
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    news_data["title"],
                    news_data.get("content", ""),
                    news_data["source_site"],
                    news_data["url"],
                    news_data["published_at"],
                    scraped_at,
                    news_data.get("is_marked_important", False),
                    news_data.get("site_importance_flag", ""),
                    INCOMING_STAGE,
                    news_data.get("type", "news"),
                    news_data.get("author", ""),
                ),
            )
            return cursor.lastrowid
        except Exception as exc:
            print(f"Insert failed: {exc}")
            return None

    def update_news(self, news_id: int, updates: Dict):
        try:
            if "content" in updates and updates["content"]:
                updates["content"] = self._normalize_news_content(updates["content"])
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [news_id]
            self.execute(f"UPDATE news SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", tuple(values))
        except Exception as exc:
            print(f"Update failed: {exc}")

    def delete_news(self, news_id: int) -> bool:
        try:
            cursor = self.execute("DELETE FROM news WHERE id = ?", (news_id,))
            return cursor.rowcount > 0
        except Exception as exc:
            print(f"Delete failed: {exc}")
            return False

    def delete_by_source_url(self, source_url: str):
        self.execute("DELETE FROM news WHERE source_url = ?", (source_url,))

    def reset_to_incoming_by_source_url(self, source_url: str) -> bool:
        try:
            cursor = self.execute(
                """
                UPDATE news
                SET stage = ?, is_duplicate = 0, duplicate_of = NULL, is_local_duplicate = 0
                WHERE source_url = ?
                """,
                (INCOMING_STAGE, source_url),
            )
            return cursor.rowcount > 0
        except Exception as exc:
            print(f"Reset news to incoming failed: {exc}")
            return False

    def mark_duplicate(self, news_id: int, master_id: int | None) -> bool:
        try:
            cursor = self.execute(
                """
                UPDATE news
                SET stage = ?, is_duplicate = 1, duplicate_of = ?, is_local_duplicate = 1
                WHERE id = ?
                """,
                (DUPLICATE_STAGE, master_id, news_id),
            )
            return cursor.rowcount > 0
        except Exception as exc:
            print(f"Mark duplicate failed: {exc}")
            return False

    def mark_archived(self, news_id: int):
        self.execute("UPDATE news SET stage = ? WHERE id = ?", (ARCHIVED_STAGE, news_id))
