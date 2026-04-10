from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional

from shared.content_contract import (
    DELIVERY_STATUS_SENT,
    REVIEW_STATUS_DISCARDED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_SELECTED,
    REVIEW_TABLE,
)
from .base_repository import BaseRepository


class ReviewRepository(BaseRepository):
    def requeue_entry(self, entry_id: int) -> bool:
        try:
            cursor = self.execute(
                f"""
                UPDATE {REVIEW_TABLE}
                SET review_status = ?, review_reason = NULL, review_summary = NULL,
                    review_score = NULL, review_category = NULL, review_tags = NULL
                WHERE id = ?
                """,
                (REVIEW_STATUS_PENDING, entry_id),
            )
            return cursor.rowcount > 0
        except Exception as exc:
            print(f"恢复审核项失败: {exc}")
            return False

    def requeue_reviewed_entries(self, content_kind: str = "news") -> int:
        try:
            cursor = self.execute(
                f"""
                UPDATE {REVIEW_TABLE}
                SET review_status = ?, review_reason = NULL, review_summary = NULL,
                    review_score = NULL, review_category = NULL, review_tags = NULL
                WHERE content_type = ? AND review_status IN (?, ?)
                """,
                (REVIEW_STATUS_PENDING, content_kind, REVIEW_STATUS_SELECTED, REVIEW_STATUS_DISCARDED),
            )
            return cursor.rowcount
        except Exception as exc:
            print(f"批量恢复审核结果失败: {exc}")
            return 0

    def clear_review_results(self, content_kind: str = "news") -> int:
        return self.requeue_reviewed_entries(content_kind)

    def save_review_result(
        self,
        entry_id: int,
        review_status: str,
        review_reason: str,
        review_score: Optional[int] = None,
        review_category: Optional[str] = None,
        review_summary: Optional[str] = None,
        review_tags: Optional[str] = None,
    ) -> None:
        self.execute(
            f"""
            UPDATE {REVIEW_TABLE}
            SET review_status = ?, review_reason = ?, review_score = ?, review_category = ?,
                review_summary = ?, review_tags = ?
            WHERE id = ?
            """,
            (review_status, review_reason, review_score, review_category, review_summary, review_tags, entry_id),
        )

    def delete_by_source_url(self, source_url: str) -> bool:
        try:
            self.execute(f"DELETE FROM {REVIEW_TABLE} WHERE source_url = ?", (source_url,))
            return True
        except Exception as exc:
            print(f"删除审核项失败: {exc}")
            return False

    def delete_entry(self, entry_id: int) -> bool:
        try:
            cursor = self.execute(f"DELETE FROM {REVIEW_TABLE} WHERE id = ?", (entry_id,))
            return cursor.rowcount > 0
        except Exception as exc:
            print(f"删除审核项失败: {exc}")
            return False

    def create_pending_entry(self, archive_row: Dict, queued_at: str) -> bool:
        try:
            self.execute(
                f"""
                INSERT INTO {REVIEW_TABLE} (
                    id, title, content, source_site, source_url, published_at, scraped_at, archived_at,
                    queued_at, is_marked_important, site_importance_flag, review_status, content_type, source_item_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    archive_row["id"],
                    archive_row["title"],
                    archive_row["content"],
                    archive_row["source_site"],
                    archive_row["source_url"],
                    archive_row["published_at"],
                    archive_row["scraped_at"],
                    archive_row["archived_at"],
                    queued_at,
                    archive_row["is_marked_important"],
                    archive_row["site_importance_flag"],
                    REVIEW_STATUS_PENDING,
                    archive_row["content_type"],
                    archive_row["source_item_id"],
                ),
            )
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as exc:
            print(f"创建待审核项失败: {exc}")
            return False

    def mark_delivered(self, entry_ids: List[int]) -> None:
        if not entry_ids:
            return
        placeholders = ",".join(["?" for _ in entry_ids])
        self.execute(
            f"UPDATE {REVIEW_TABLE} SET delivery_status = ?, delivered_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
            tuple([DELIVERY_STATUS_SENT, *entry_ids]),
        )
