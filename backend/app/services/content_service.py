from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from shared.content_contract import (
    ARCHIVE_TABLE,
    ARCHIVE_STATUS_BLOCKED,
    ARCHIVE_STATUS_READY,
    EXPORT_SCOPE_ARCHIVE,
    EXPORT_SCOPE_BLOCKED,
    EXPORT_SCOPE_DISCARDED,
    EXPORT_SCOPE_INCOMING,
    EXPORT_SCOPE_REVIEW,
    EXPORT_SCOPE_SELECTED,
    INCOMING_STAGE,
    REVIEW_STATUS_DISCARDED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_SELECTED,
    REVIEW_TABLE,
)
from ..core.exceptions import BusinessError, DatabaseError
from ..infrastructure.repositories import repositories


class ContentService:
    @staticmethod
    def _repos():
        return repositories()

    def get_source_stats(self, content_kind: str = "news") -> Dict:
        try:
            return self._repos().news_admin.get_stats(content_kind)
        except Exception as exc:
            raise DatabaseError(f"查询统计失败: {str(exc)}") from exc

    def get_dashboard_overview(self, content_kind: str = "news") -> Dict:
        repos = self._repos()
        row = repos.news_admin.execute(
            f"""
            SELECT
                (SELECT COUNT(*) FROM news WHERE stage = ? AND type = ?) AS incoming,
                (SELECT COUNT(*) FROM {ARCHIVE_TABLE} WHERE content_type = ? AND archive_status = ?) AS archive,
                (SELECT COUNT(*) FROM {ARCHIVE_TABLE} WHERE content_type = ? AND archive_status = ?) AS blocked,
                (SELECT COUNT(*) FROM {REVIEW_TABLE} WHERE content_type = ? AND review_status = ?) AS review,
                (SELECT COUNT(*) FROM {REVIEW_TABLE} WHERE content_type = ? AND review_status = ?) AS selected,
                (SELECT COUNT(*) FROM {REVIEW_TABLE} WHERE content_type = ? AND review_status = ?) AS discarded
            """,
            (
                INCOMING_STAGE,
                content_kind,
                content_kind,
                ARCHIVE_STATUS_READY,
                content_kind,
                ARCHIVE_STATUS_BLOCKED,
                content_kind,
                REVIEW_STATUS_PENDING,
                content_kind,
                REVIEW_STATUS_SELECTED,
                content_kind,
                REVIEW_STATUS_DISCARDED,
            ),
        ).fetchone()
        if not row:
            return {"incoming": 0, "archive": 0, "blocked": 0, "review": 0, "selected": 0, "discarded": 0}
        return {
            "incoming": row["incoming"],
            "archive": row["archive"],
            "blocked": row["blocked"],
            "review": row["review"],
            "selected": row["selected"],
            "discarded": row["discarded"],
        }

    def list_source_groups(self, page: int, limit: int, source: Optional[str], keyword: Optional[str], content_kind: str) -> Dict:
        return self._repos().news_source_groups.get_source_groups(page, limit, source, keyword, content_kind)

    def list_incoming(self, page: int, limit: int, source: Optional[str], keyword: Optional[str], content_kind: str) -> Dict:
        return self._repos().news_admin.get_incoming_news(page, limit, source, keyword, content_kind)

    def list_archive(self, page: int, limit: int, source: Optional[str], keyword: Optional[str], content_kind: str) -> Dict:
        return self._repos().archive_query.list_entries(page, limit, source, keyword, content_kind, ARCHIVE_STATUS_READY)

    def list_blocked(self, page: int, limit: int, keyword: Optional[str], content_kind: str) -> Dict:
        return self._repos().archive_query.list_entries(page, limit, None, keyword, content_kind, ARCHIVE_STATUS_BLOCKED)

    def list_review_queue(self, page: int, limit: int, source: Optional[str], keyword: Optional[str], content_kind: str) -> Dict:
        return self._repos().review_admin.list_entries(page, limit, source, keyword, content_kind, REVIEW_STATUS_PENDING)

    def list_review_decisions(self, decision: str, page: int, limit: int, source: Optional[str], keyword: Optional[str], content_kind: str) -> Dict:
        if decision not in (REVIEW_STATUS_SELECTED, REVIEW_STATUS_DISCARDED):
            raise BusinessError("无效的审核决策类型")
        return self._repos().review_admin.list_entries(page, limit, source, keyword, content_kind, decision)

    def export_content(
        self,
        scope: str,
        start_date: Optional[str],
        end_date: Optional[str],
        keyword: Optional[str],
        source: Optional[str],
        content_kind: Optional[str],
        fields: Optional[str],
    ):
        repos = self._repos()
        if scope == EXPORT_SCOPE_INCOMING:
            payload = repos.news_admin.get_incoming_news_for_export(start_date, end_date, keyword, source, content_kind)
        elif scope == EXPORT_SCOPE_ARCHIVE:
            payload = repos.archive_query.export_entries(start_date, end_date, keyword, source, content_kind, ARCHIVE_STATUS_READY)
        elif scope == EXPORT_SCOPE_BLOCKED:
            payload = repos.archive_query.export_entries(start_date, end_date, keyword, source, content_kind, ARCHIVE_STATUS_BLOCKED)
        elif scope == EXPORT_SCOPE_REVIEW:
            payload = repos.review_admin.list_entries(page=1, limit=10000, source=source, keyword=keyword, content_kind=content_kind or "news", review_status=REVIEW_STATUS_PENDING)["results"]
        elif scope == EXPORT_SCOPE_SELECTED:
            payload = repos.review_admin.list_entries(page=1, limit=10000, source=source, keyword=keyword, content_kind=content_kind or "news", review_status=REVIEW_STATUS_SELECTED)["results"]
        elif scope == EXPORT_SCOPE_DISCARDED:
            payload = repos.review_admin.list_entries(page=1, limit=10000, source=source, keyword=keyword, content_kind=content_kind or "news", review_status=REVIEW_STATUS_DISCARDED)["results"]
        else:
            raise BusinessError("无效的导出范围")

        field_list = [field.strip() for field in fields.split(",")] if fields else []
        return [{key: item[key] for key in field_list if key in item} if field_list else item for item in payload]

    def get_export_filename(self) -> str:
        return f"ainews_export_{datetime.now().strftime('%Y%m%d%H%M')}.json"

content_service = ContentService()
