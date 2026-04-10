from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from shared.content_contract import ARCHIVE_STATUS_BLOCKED, ARCHIVE_STATUS_REVIEWED
from ..infrastructure.repositories import transactional_repositories
from .system_settings_service import system_settings_service


class ContentTransitionService:
    def persist_deduplication_results(self, marked_news: List[Dict], delete_duplicates: bool = False) -> List[Dict]:
        persisted_news = marked_news
        duplicates = [item for item in marked_news if item.get("is_local_duplicate", False)]

        with transactional_repositories() as tx_repos:
            if delete_duplicates:
                for duplicate in duplicates:
                    tx_repos.news.delete_news(duplicate["id"])
                persisted_news = [item for item in marked_news if not item.get("is_local_duplicate", False)]

            for news in persisted_news:
                if news.get("is_local_duplicate", False):
                    tx_repos.news.mark_duplicate(news["id"], news.get("duplicate_of"))
                    continue
                tx_repos.archive.create_entry(news)
                tx_repos.news.mark_archived(news["id"])

        return persisted_news

    def apply_blocklist(self, time_range_hours: int, content_kind: str) -> Dict:
        start_time = "1970-01-01 00:00:00" if time_range_hours <= 0 else (datetime.now() - timedelta(hours=time_range_hours)).strftime("%Y-%m-%d %H:%M:%S")
        blocked_at = system_settings_service.get_system_time().strftime("%Y-%m-%d %H:%M:%S")

        with transactional_repositories() as tx_repos:
            keywords = tx_repos.blacklist.get_blacklist_keywords(content_kind)
            archive_rows = tx_repos.archive_query.list_filter_candidates(start_time, content_kind)
            scanned_count = len(archive_rows)
            blocked_count = 0
            review_count = 0

            for row in archive_rows:
                filter_reason = tx_repos.blacklist.match_keyword((row["title"] or "").lower(), keywords)
                if filter_reason:
                    tx_repos.archive.update_status(
                        row["id"],
                        ARCHIVE_STATUS_BLOCKED,
                        block_reason=filter_reason,
                        archived_at=blocked_at,
                    )
                    blocked_count += 1
                    continue

                tx_repos.review.create_pending_entry(row, blocked_at)
                tx_repos.archive.update_status(
                    row["id"],
                    ARCHIVE_STATUS_REVIEWED,
                    block_reason=None,
                )
                review_count += 1

            retroactive_blocked_count = 0
            review_rows = tx_repos.review_admin.list_recent_entries(start_time, content_kind)
            for row in review_rows:
                filter_reason = tx_repos.blacklist.match_keyword((row["title"] or "").lower(), keywords)
                if not filter_reason:
                    continue
                tx_repos.review.delete_entry(row["id"])
                tx_repos.archive.update_status_by_source_url(
                    row["source_url"],
                    ARCHIVE_STATUS_BLOCKED,
                    block_reason=filter_reason,
                    archived_at=blocked_at,
                )
                retroactive_blocked_count += 1

        return {
            "scanned": scanned_count,
            "blocked": blocked_count + retroactive_blocked_count,
            "review": review_count,
            "retroactive": retroactive_blocked_count,
        }


content_transition_service = ContentTransitionService()
