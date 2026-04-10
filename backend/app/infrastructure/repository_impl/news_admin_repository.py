from __future__ import annotations

from typing import Dict, List, Optional

from shared.content_contract import INCOMING_STAGE
from .base_repository import BaseRepository


class NewsAdminRepository(BaseRepository):
    def get_incoming_news(
        self,
        page: int = 1,
        limit: int = 50,
        source_site: Optional[str] = None,
        keyword: Optional[str] = None,
        type_filter: str = "news",
    ) -> Dict:
        try:
            offset = (page - 1) * limit
            query = """
                SELECT n.*, m.title as master_title, m.id as master_id_ref
                FROM news n
                LEFT JOIN news m ON n.duplicate_of = m.id
                WHERE n.stage = ? AND n.type = ?
            """
            params: List[object] = [INCOMING_STAGE, type_filter]

            if source_site:
                query += " AND n.source_site = ?"
                params.append(source_site)
            if keyword:
                query += " AND (n.title LIKE ? OR n.content LIKE ?)"
                term = f"%{keyword}%"
                params.extend([term, term])

            data_query = query + " ORDER BY n.published_at DESC LIMIT ? OFFSET ?"
            cursor = self.execute(data_query, tuple(params + [limit, offset]))
            rows = cursor.fetchall()
            count_cursor = self.execute(f"SELECT count(*) as total FROM ({query})", tuple(params))
            total = count_cursor.fetchone()["total"]
            return {"results": [dict(row) for row in rows], "total": total, "page": page, "limit": limit}
        except Exception as exc:
            print(f"Get incoming news failed: {exc}")
            return {"results": [], "total": 0, "page": page, "limit": limit}

    def get_stats(self, type_filter: str = "news") -> Dict:
        try:
            cursor = self.execute(
                "SELECT source_site, COUNT(*) as count FROM news WHERE type = ? AND stage = ? GROUP BY source_site",
                (type_filter, INCOMING_STAGE),
            )
            rows = cursor.fetchall()
            return {"stats": [{"source": row["source_site"], "count": row["count"]} for row in rows]}
        except Exception as exc:
            print(f"Get stats failed: {exc}")
            return {"stats": []}

    def get_incoming_news_for_export(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        keywords: Optional[str] = None,
        source_site: Optional[str] = None,
        content_kind: Optional[str] = None,
    ) -> List[Dict]:
        try:
            sql = "SELECT * FROM news WHERE stage = ?"
            params: List[object] = [INCOMING_STAGE]

            if content_kind:
                sql += " AND type = ?"
                params.append(content_kind)
            if start_date:
                sql += " AND published_at >= ?"
                params.append(start_date)
            if end_date:
                sql += " AND published_at <= ?"
                params.append(end_date)
            if source_site:
                sql += " AND source_site = ?"
                params.append(source_site)
            if keywords:
                term = f"%{keywords}%"
                sql += " AND (title LIKE ? OR content LIKE ?)"
                params.extend([term, term])
            sql += " ORDER BY published_at DESC"
            cursor = self.execute(sql, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            print(f"Export query failed: {exc}")
            return []
