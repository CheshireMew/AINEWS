from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from shared.content_contract import REVIEW_STATUS_PENDING, REVIEW_STATUS_SELECTED, REVIEW_TABLE
from .base_repository import BaseRepository


class ReviewAdminRepository(BaseRepository):
    def list_entries(
        self,
        page: int = 1,
        limit: int = 50,
        source: Optional[str] = None,
        keyword: Optional[str] = None,
        content_kind: str = "news",
        review_status: Optional[str] = None,
    ) -> Dict:
        where = "content_type = ?"
        params = [content_kind]

        if review_status:
            where += " AND review_status = ?"
            params.append(review_status)
        if source:
            where += " AND source_site = ?"
            params.append(source)
        if keyword:
            where += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.extend([term, term])

        return self.paginated_query(
            table=REVIEW_TABLE,
            fields="id, title, content, source_site, source_url, published_at, scraped_at, archived_at, queued_at, is_marked_important, site_importance_flag, review_status, review_summary, review_reason, review_score, review_category, review_tags, delivery_status, delivered_at, content_type, source_item_id",
            where=where,
            where_params=tuple(params),
            order_by="published_at DESC",
            page=page,
            limit=limit,
        )

    def export_selected_entries(self, hours: int, min_score: int, content_kind: str = "news") -> Dict:
        cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.execute(
            f"""
            SELECT id, title, source_url, review_reason, published_at, review_status, review_summary, review_score, review_category
            FROM {REVIEW_TABLE}
            WHERE published_at >= ? AND content_type = ? AND review_status = ? AND COALESCE(review_score, 0) >= ?
            ORDER BY published_at DESC
            """,
            (cutoff_time, content_kind, REVIEW_STATUS_SELECTED, min_score),
        )
        items = [dict(row) for row in cursor.fetchall()]
        return {
            "items": items,
            "metadata": {
                "count": len(items),
                "time_range_hours": hours,
                "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

    def get_pending_entries(self, cutoff_time: str, content_kind: str, limit: int = 10) -> List[Dict]:
        cursor = self.execute(
            f"""
            SELECT id, title, content
            FROM {REVIEW_TABLE}
            WHERE published_at >= ? AND review_status = ? AND content_type = ?
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (cutoff_time, REVIEW_STATUS_PENDING, content_kind, limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def count_pending_entries(self, cutoff_time: str, content_kind: str) -> int:
        cursor = self.execute(
            f"SELECT COUNT(*) as total FROM {REVIEW_TABLE} WHERE published_at >= ? AND review_status = ? AND content_type = ?",
            (cutoff_time, REVIEW_STATUS_PENDING, content_kind),
        )
        row = cursor.fetchone()
        return row["total"] if row else 0

    def get_source_url(self, entry_id: int) -> Optional[str]:
        try:
            cursor = self.execute(f"SELECT source_url FROM {REVIEW_TABLE} WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            return row["source_url"] if row else None
        except Exception as exc:
            print(f"获取审核项链接失败: {exc}")
            return None

    def list_recent_entries(self, start_time: str, content_kind: str) -> List[Dict]:
        cursor = self.execute(
            f"""
            SELECT id, title, source_url
            FROM {REVIEW_TABLE}
            WHERE queued_at >= ? AND content_type = ?
            """,
            (start_time, content_kind),
        )
        return [dict(row) for row in cursor.fetchall()]
