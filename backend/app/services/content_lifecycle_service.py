from __future__ import annotations

from typing import Dict, Optional

from shared.content_contract import CONTENT_KINDS
from ..core.exceptions import BusinessError
from ..infrastructure.repositories import repositories, transactional_repositories
from .ai_pipeline_service import ai_pipeline_service
from .automation_settings_service import automation_settings_service
from .deduplication_service import deduplication_service
from .review_settings_service import review_settings_service
from .scraper_run_service import scraper_run_service
from .telegram_delivery_service import telegram_delivery_service
from .content_transition_service import content_transition_service


class ContentLifecycleService:
    @staticmethod
    def _repos():
        return repositories()

    def delete_incoming_entry(self, entry_id: int) -> bool:
        return self._repos().news.delete_news(entry_id)

    def delete_archive_entry(self, entry_id: int) -> bool:
        return self._delete_content_chain(self._repos().archive_query.get_source_url(entry_id))

    def delete_review_entry(self, entry_id: int) -> bool:
        return self._delete_content_chain(self._repos().review_admin.get_source_url(entry_id))

    def restore_archive_entry(self, entry_id: int) -> bool:
        with transactional_repositories() as tx_repos:
            source_url = tx_repos.archive_query.get_source_url(entry_id)
            if not source_url:
                return False
            tx_repos.archive.delete_by_source_url(source_url)
            tx_repos.review.delete_by_source_url(source_url)
            return tx_repos.news.reset_to_incoming_by_source_url(source_url)

    def restore_blocked_entry(self, entry_id: int) -> bool:
        return self._repos().archive.restore_blocked_entry(entry_id)

    def restore_blocked_queue(self, content_kind: str = "news") -> Dict:
        return {"restored_count": self._repos().archive.restore_blocked_entries(content_kind)}

    def apply_blocklist(self, time_range_hours: int, content_kind: str) -> Dict:
        return {"stats": content_transition_service.apply_blocklist(time_range_hours, content_kind)}

    def reset_review_item(self, entry_id: int) -> Dict:
        success = self._repos().review.requeue_entry(entry_id)
        if not success:
            raise BusinessError("恢复失败")
        return {"message": "恢复成功"}

    def reset_review_queue(self, content_kind: str = "news") -> Dict:
        return {"restored_count": self._repos().review.requeue_reviewed_entries(content_kind)}

    def clear_review_results(self, content_kind: str = "news") -> Dict:
        return {"cleared_count": self._repos().review.clear_review_results(content_kind)}

    async def run_review(self, filter_prompt: str, hours: int, content_kind: str = "news") -> Dict:
        return await ai_pipeline_service.run_content_review(filter_prompt, hours, content_kind)

    async def run_automation_cycle(self) -> None:
        await scraper_run_service.wait_for_scrapers()
        for content_kind in CONTENT_KINDS:
            await deduplication_service.auto_deduplication(content_kind=content_kind)
            self.apply_blocklist(automation_settings_service.get_window(content_kind)["filter_hours"], content_kind)
            review_config = review_settings_service.get_config(content_kind)
            if review_config["prompt"]:
                await self.run_review(review_config["prompt"], review_config["hours"], content_kind)
        await telegram_delivery_service.auto_telegram_push()

    def _delete_content_chain(self, source_url: Optional[str]) -> bool:
        if not source_url:
            return False
        with transactional_repositories() as tx_repos:
            tx_repos.news.delete_by_source_url(source_url)
            tx_repos.archive.delete_by_source_url(source_url)
            tx_repos.review.delete_by_source_url(source_url)
            return True


content_lifecycle_service = ContentLifecycleService()
