from __future__ import annotations

from typing import Dict, List
import sqlite3

from shared.content_contract import (
    ARCHIVE_STATUS_BLOCKED,
    ARCHIVE_STATUS_READY,
    ARCHIVE_TABLE,
)
from .base_repository import BaseRepository
from .time_utils import get_beijing_time

_UNSET = object()


class ArchiveRepository(BaseRepository):
    def create_entry(self, news: Dict) -> None:
        self.execute(
            f"""
            INSERT OR IGNORE INTO {ARCHIVE_TABLE} (
                id, title, content, source_site, source_url, published_at, scraped_at, archived_at,
                is_marked_important, site_importance_flag, archive_status, content_type, source_item_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
            """,
            (
                news["id"],
                news["title"],
                news["content"],
                news["source_site"],
                news["source_url"],
                news["published_at"],
                news["scraped_at"],
                news.get("is_marked_important", False),
                news.get("site_importance_flag", ""),
                ARCHIVE_STATUS_READY,
                news.get("type", "news"),
                news["id"],
            ),
        )

    def update_status(
        self,
        entry_id: int,
        archive_status: str,
        *,
        block_reason=_UNSET,
        restored_from_blocklist=_UNSET,
        archived_at=_UNSET,
    ) -> bool:
        return self._update_status("id = ?", (entry_id,), archive_status, block_reason, restored_from_blocklist, archived_at)

    def update_status_by_source_url(
        self,
        source_url: str,
        archive_status: str,
        *,
        block_reason=_UNSET,
        restored_from_blocklist=_UNSET,
        archived_at=_UNSET,
    ) -> bool:
        return self._update_status("source_url = ?", (source_url,), archive_status, block_reason, restored_from_blocklist, archived_at)

    def restore_blocked_entries(self, content_kind: str = "news") -> int:
        try:
            cursor = self.execute(
                f"""
                UPDATE {ARCHIVE_TABLE}
                SET archive_status = ?, restored_from_blocklist = 1
                WHERE content_type = ? AND archive_status = ?
                """,
                (ARCHIVE_STATUS_READY, content_kind, ARCHIVE_STATUS_BLOCKED),
            )
            return cursor.rowcount
        except Exception as exc:
            print(f"批量恢复已拦截内容失败: {exc}")
            return 0

    def restore_blocked_entry(self, entry_id: int) -> bool:
        try:
            cursor = self.execute(
                f"""
                UPDATE {ARCHIVE_TABLE}
                SET archive_status = ?, restored_from_blocklist = 1
                WHERE id = ? AND archive_status = ?
                """,
                (ARCHIVE_STATUS_READY, entry_id, ARCHIVE_STATUS_BLOCKED),
            )
            return cursor.rowcount > 0
        except Exception as exc:
            print(f"恢复单条已拦截内容失败: {exc}")
            return False

    def _update_status(
        self,
        where_clause: str,
        where_params: tuple,
        archive_status: str,
        block_reason,
        restored_from_blocklist,
        archived_at,
    ) -> bool:
        updates = ["archive_status = ?"]
        params: List[object] = [archive_status]

        if block_reason is not _UNSET:
            updates.append("block_reason = ?")
            params.append(block_reason)
        if restored_from_blocklist is not _UNSET:
            updates.append("restored_from_blocklist = ?")
            params.append(restored_from_blocklist)
        if archived_at is not _UNSET:
            updates.append("archived_at = ?")
            params.append(archived_at if archived_at is not None else get_beijing_time().strftime("%Y-%m-%d %H:%M:%S"))

        cursor = self.execute(
            f"UPDATE {ARCHIVE_TABLE} SET {', '.join(updates)} WHERE {where_clause}",
            tuple([*params, *where_params]),
        )
        return cursor.rowcount > 0

    def delete_by_source_url(self, source_url: str) -> bool:
        try:
            self.execute(f"DELETE FROM {ARCHIVE_TABLE} WHERE source_url = ?", (source_url,))
            return True
        except sqlite3.Error as exc:
            print(f"删除归档内容失败: {exc}")
            return False
