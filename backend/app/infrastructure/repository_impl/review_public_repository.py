from __future__ import annotations

from typing import Dict

from shared.content_contract import DELIVERY_STATUS_SENT, REVIEW_STATUS_SELECTED, REVIEW_TABLE
from .base_repository import BaseRepository


class ReviewPublicRepository(BaseRepository):
    def list_public_entries(self, content_kind: str, limit: int = 20, offset: int = 0) -> Dict:
        days = 3 if content_kind == "news" else 7
        count_cursor = self.execute(
            f"""
            SELECT COUNT(*) as total FROM {REVIEW_TABLE}
            WHERE content_type = ? AND review_status = ? AND delivery_status = ?
              AND published_at >= datetime('now', ?)
            """,
            (content_kind, REVIEW_STATUS_SELECTED, DELIVERY_STATUS_SENT, f"-{days} days"),
        )
        total = count_cursor.fetchone()["total"]
        cursor = self.execute(
            f"""
            SELECT id, title, source_url, published_at, source_site, review_category, review_reason, review_summary, review_score
            FROM {REVIEW_TABLE}
            WHERE content_type = ? AND review_status = ? AND delivery_status = ?
              AND published_at >= datetime('now', ?)
            ORDER BY published_at DESC LIMIT ? OFFSET ?
            """,
            (content_kind, REVIEW_STATUS_SELECTED, DELIVERY_STATUS_SENT, f"-{days} days", limit, offset),
        )
        return {"items": [dict(row) for row in cursor.fetchall()], "total": total, "limit": limit, "offset": offset}

    def search_public_entries(self, query_text: str, content_kind: str = "all", limit: int = 20, offset: int = 0) -> Dict:
        search_term = f"%{query_text}%"
        params = [REVIEW_STATUS_SELECTED, DELIVERY_STATUS_SENT]
        where_parts = ["review_status = ?", "delivery_status = ?"]

        if content_kind == "news":
            where_parts.append("content_type = 'news'")
            where_parts.append("published_at >= datetime('now', '-3 days')")
        elif content_kind == "article":
            where_parts.append("content_type = 'article'")
            where_parts.append("published_at >= datetime('now', '-7 days')")
        else:
            where_parts.append("((content_type = 'news' AND published_at >= datetime('now', '-3 days')) OR (content_type = 'article' AND published_at >= datetime('now', '-7 days')))")

        where_parts.append("(title LIKE ? OR content LIKE ?)")
        params.extend([search_term, search_term])
        where_clause = " AND ".join(where_parts)

        count_cursor = self.execute(f"SELECT COUNT(*) as total FROM {REVIEW_TABLE} WHERE {where_clause}", tuple(params))
        total = count_cursor.fetchone()["total"]
        cursor = self.execute(
            f"""
            SELECT id, title, content, source_url, published_at, source_site, content_type, review_summary, review_score
            FROM {REVIEW_TABLE}
            WHERE {where_clause}
            ORDER BY published_at DESC LIMIT ? OFFSET ?
            """,
            tuple(params + [limit, offset]),
        )
        return {"items": [dict(row) for row in cursor.fetchall()], "total": total, "limit": limit, "offset": offset, "query": query_text}
