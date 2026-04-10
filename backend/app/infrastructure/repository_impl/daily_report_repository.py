from __future__ import annotations

from typing import Dict, List, Optional

from .base_repository import BaseRepository


class DailyReportRepository(BaseRepository):
    def save_report(self, date: str, report_type: str, title: str, content: str, news_count: int) -> None:
        self.execute(
            "INSERT OR REPLACE INTO daily_reports (date, type, title, content, news_count) VALUES (?, ?, ?, ?, ?)",
            (date, report_type, title, content, news_count),
        )

    def list_reports(self, report_type: Optional[str], limit: int, offset: int) -> Dict:
        params: List[object] = []
        where_parts: List[str] = []

        if report_type:
            where_parts.append("type = ?")
            params.append(report_type)

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        total_cursor = self.execute(f"SELECT COUNT(*) as total FROM daily_reports {where_clause}", tuple(params))
        total = total_cursor.fetchone()["total"]
        rows_cursor = self.execute(
            f"""
            SELECT id, date, type, title, content, news_count, created_at
            FROM daily_reports
            {where_clause}
            ORDER BY date DESC
            LIMIT ? OFFSET ?
            """,
            tuple([*params, limit, offset]),
        )
        return {
            "items": [dict(row) for row in rows_cursor.fetchall()],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
