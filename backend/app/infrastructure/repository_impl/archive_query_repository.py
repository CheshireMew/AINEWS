from __future__ import annotations

from typing import Dict, List, Optional

from shared.content_contract import ARCHIVE_STATUS_READY, ARCHIVE_TABLE
from .base_repository import BaseRepository


class ArchiveQueryRepository(BaseRepository):
    def list_entries(
        self,
        page: int = 1,
        limit: int = 50,
        source: Optional[str] = None,
        keyword: Optional[str] = None,
        content_kind: str = "news",
        archive_status: Optional[str] = None,
    ) -> Dict:
        where = "content_type = ?"
        params = [content_kind]

        if archive_status:
            where += " AND archive_status = ?"
            params.append(archive_status)
        if source:
            where += " AND source_site = ?"
            params.append(source)
        if keyword:
            where += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.extend([term, term])

        return self.paginated_query(
            table=ARCHIVE_TABLE,
            fields="id, title, content, source_site, source_url, published_at, scraped_at, archived_at, is_marked_important, site_importance_flag, archive_status, content_type, source_item_id, restored_from_blocklist, block_reason",
            where=where,
            where_params=tuple(params),
            order_by="published_at DESC",
            page=page,
            limit=limit,
        )

    def list_filter_candidates(self, start_time: str, content_kind: str) -> List[Dict]:
        cursor = self.execute(
            f"""
            SELECT id, title, content, source_site, source_url, published_at, scraped_at, archived_at,
                   is_marked_important, site_importance_flag, source_item_id, content_type
            FROM {ARCHIVE_TABLE}
            WHERE archived_at >= ? AND archive_status = ? AND content_type = ?
              AND (restored_from_blocklist IS NULL OR restored_from_blocklist = 0)
            """,
            (start_time, ARCHIVE_STATUS_READY, content_kind),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_source_url(self, entry_id: int) -> Optional[str]:
        try:
            cursor = self.execute(f"SELECT source_url FROM {ARCHIVE_TABLE} WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            return row["source_url"] if row else None
        except Exception as exc:
            print(f"获取归档内容链接失败: {exc}")
            return None

    def export_entries(
        self,
        start_date: Optional[str],
        end_date: Optional[str],
        keyword: Optional[str],
        source_site: Optional[str],
        content_kind: Optional[str],
        archive_status: Optional[str] = None,
    ) -> List[Dict]:
        where = ["1=1"]
        params: List[object] = []

        if start_date:
            where.append("published_at >= ?")
            params.append(start_date)
        if end_date:
            where.append("published_at <= ?")
            params.append(end_date)
        if source_site:
            where.append("source_site = ?")
            params.append(source_site)
        if content_kind:
            where.append("content_type = ?")
            params.append(content_kind)
        if archive_status:
            where.append("archive_status = ?")
            params.append(archive_status)
        if keyword:
            where.append("(title LIKE ? OR content LIKE ?)")
            term = f"%{keyword}%"
            params.extend([term, term])

        cursor = self.execute(
            f"SELECT * FROM {ARCHIVE_TABLE} WHERE {' AND '.join(where)} ORDER BY published_at DESC",
            tuple(params),
        )
        return [dict(row) for row in cursor.fetchall()]
