from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from shared.content_contract import INCOMING_STAGE
from .base_repository import BaseRepository


class NewsRuntimeRepository(BaseRepository):
    def get_latest_news_url(self, source_site: str) -> Optional[str]:
        try:
            cursor = self.execute(
                "SELECT source_url FROM news WHERE source_site = ? ORDER BY scraped_at DESC LIMIT 1",
                (source_site,),
            )
            row = cursor.fetchone()
            return row["source_url"] if row else None
        except Exception as exc:
            print(f"Get latest URL failed: {exc}")
            return None

    def get_recent_news_urls(self, source_site: str, limit: int = 50) -> List[str]:
        try:
            cursor = self.execute(
                "SELECT source_url FROM news WHERE source_site = ? ORDER BY scraped_at DESC LIMIT ?",
                (source_site, limit),
            )
            return [row["source_url"] for row in cursor.fetchall()]
        except Exception as exc:
            print(f"Get recent URL list failed: {exc}")
            return []

    def get_news_by_time_range(self, hours: int, type_filter: str = "news") -> List[Dict]:
        try:
            params: List[object] = [INCOMING_STAGE, type_filter]
            sql = """
                SELECT id, title, content, source_site, source_url, published_at, scraped_at,
                       is_marked_important, site_importance_flag, stage, type
                FROM news
                WHERE stage = ? AND type = ?
            """
            if hours > 0:
                threshold = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
                sql += " AND scraped_at >= ?"
                params.append(threshold)
            sql += " ORDER BY published_at DESC"
            cursor = self.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "source_site": row["source_site"],
                    "source_url": row["source_url"],
                    "url": row["source_url"],
                    "published_at": row["published_at"],
                    "scraped_at": row["scraped_at"],
                    "is_marked_important": row["is_marked_important"],
                    "site_importance_flag": row["site_importance_flag"],
                    "stage": row["stage"],
                    "type": row["type"],
                }
                for row in rows
            ]
        except Exception as exc:
            print(f"Get news by time range failed: {exc}")
            return []

    def get_news_by_ids(self, news_ids: List[int]) -> List[Dict]:
        if not news_ids:
            return []
        try:
            placeholders = ",".join(["?" for _ in news_ids])
            cursor = self.execute(f"SELECT id, title FROM news WHERE id IN ({placeholders})", tuple(news_ids))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"Get news by ids failed: {exc}")
            return []

    def get_incoming_news_since(self, cutoff_time: str, type_filter: str) -> List[Dict]:
        try:
            cursor = self.execute(
                """
                SELECT id, title, content, source_url, source_site, published_at, scraped_at, type
                FROM news
                WHERE stage = ? AND scraped_at >= ? AND type = ?
                ORDER BY scraped_at DESC
                """,
                (INCOMING_STAGE, cutoff_time, type_filter),
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"Get incoming news since failed: {exc}")
            return []
