from __future__ import annotations

from typing import Dict, List

from shared.content_contract import REVIEW_STATUS_SELECTED, REVIEW_TABLE
from .base_repository import BaseRepository


class ReviewDeliveryRepository(BaseRepository):
    def get_ranked_entries(self, start_time: str, content_kind: str) -> List[Dict]:
        cursor = self.execute(
            f"""
            SELECT id, title, source_url, review_reason, review_score, review_status
            FROM {REVIEW_TABLE}
            WHERE published_at >= ? AND content_type = ? AND review_status = ?
            ORDER BY COALESCE(review_score, 0) DESC, published_at DESC
            """,
            (start_time, content_kind, REVIEW_STATUS_SELECTED),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_entries_by_ids(self, entry_ids: List[int]) -> List[Dict]:
        if not entry_ids:
            return []
        placeholders = ",".join(["?" for _ in entry_ids])
        cursor = self.execute(
            f"SELECT id, title, source_url, content, content_type FROM {REVIEW_TABLE} WHERE id IN ({placeholders})",
            tuple(entry_ids),
        )
        return [dict(row) for row in cursor.fetchall()]
