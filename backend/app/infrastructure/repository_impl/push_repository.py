from __future__ import annotations

from typing import Dict, List

from shared.content_contract import DELIVERY_STATUS_PENDING, REVIEW_STATUS_SELECTED, REVIEW_TABLE
from .base_repository import BaseRepository


class PushRepository(BaseRepository):
    def get_pending_review_entries(self, content_kind: str = "news") -> List[Dict]:
        try:
            cursor = self.execute(
                f"""
                SELECT r.*
                FROM {REVIEW_TABLE} r
                LEFT JOIN push_logs p ON r.id = p.news_id AND p.status = 'success'
                WHERE p.id IS NULL
                  AND r.content_type = ?
                  AND r.review_status = ?
                  AND r.delivery_status = ?
                  AND r.queued_at >= datetime('now', '-24 hours')
                ORDER BY r.queued_at ASC
                """,
                (content_kind, REVIEW_STATUS_SELECTED, DELIVERY_STATUS_PENDING),
            )
            return [dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"Get Pending Review Entries Error: {exc}")
            return []

    def log_push_status(self, news_id: int, platform: str, status: str, message: str = None) -> bool:
        try:
            self.execute(
                "INSERT INTO push_logs (news_id, platform, status, message) VALUES (?, ?, ?, ?)",
                (news_id, platform, status, message),
            )
            return True
        except Exception as exc:
            print(f"Log Push Error: {exc}")
            return False
