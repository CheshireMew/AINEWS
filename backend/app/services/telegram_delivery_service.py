from __future__ import annotations

from datetime import timedelta
from typing import Dict, List

from shared.content_contract import (
    CONTENT_KIND_ARTICLE,
    CONTENT_KIND_NEWS,
    DELIVERY_STATUS_SENT,
    delivery_key,
)
from ..core.exceptions import ValidationError
from ..infrastructure.repositories import repositories
from .telegram_gateway_service import telegram_gateway_service
from .telegram_message_service import telegram_message_service


class TelegramDeliveryService:
    @staticmethod
    def _repos():
        return repositories()

    def _target_time_reached(self, content_kind: str, now) -> tuple[bool, str]:
        target_time_str = self._repos().config.get_config(delivery_key(content_kind, "time")) or ("21:00" if content_kind == CONTENT_KIND_ARTICLE else "20:00")
        try:
            target_hour, target_minute = map(int, target_time_str.split(":"))
        except Exception:
            target_hour, target_minute = (21, 0) if content_kind == CONTENT_KIND_ARTICLE else (20, 0)
        return now.hour * 60 + now.minute >= target_hour * 60 + target_minute, target_time_str

    def _last_delivery_key(self, content_kind: str) -> str:
        return delivery_key(content_kind, "last_date")

    async def _auto_daily_push(self, content_kind: str, force: bool = False) -> Dict:
        repos = self._repos()
        now = repos.config.get_system_time()
        if not force:
            reached, target_time_str = self._target_time_reached(content_kind, now)
            if not reached:
                return {"status": "skipped", "message": f"Not push time yet (Current: {now.strftime('%H:%M')}, Target: {target_time_str})"}
            today_str = now.strftime("%Y-%m-%d")
            if repos.config.get_config(self._last_delivery_key(content_kind)) == today_str:
                return {"status": "skipped", "message": "Already pushed today"}

        start_time = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        entries = [item for item in repos.review_delivery.get_ranked_entries(start_time, content_kind) if (item.get("review_score") or 0) >= 5]
        if not entries:
            if not force:
                repos.config.set_config(self._last_delivery_key(content_kind), now.strftime("%Y-%m-%d"))
            return {"status": "skipped", "message": "No content found"}

        report_title, report_items = telegram_message_service.build_daily_report(entries, content_kind, now)
        report_content = telegram_message_service.compose_daily_report_part(report_title, report_items)
        parts = telegram_message_service.split_daily_report_parts(report_title, report_items)
        await telegram_gateway_service.send_many_or_raise(parts, "Telegram 日报发送失败，请检查 Bot 配置和网络连接")

        repos.daily_reports.save_report(now.strftime("%Y-%m-%d"), content_kind, report_title, report_content, len(report_items))
        if not force:
            repos.config.set_config(self._last_delivery_key(content_kind), now.strftime("%Y-%m-%d"))
        return {"status": "success", "count": len(report_items), "parts": len(parts), "message": f"Pushed {len(report_items)} items"}

    async def auto_daily_best_push(self, force: bool = False) -> Dict:
        return await self._auto_daily_push(CONTENT_KIND_NEWS, force)

    async def auto_daily_article_push(self, force: bool = False) -> Dict:
        return await self._auto_daily_push(CONTENT_KIND_ARTICLE, force)

    async def auto_telegram_push(self):
        if not telegram_gateway_service.has_bot_config():
            return

        sent_ids: List[int] = []
        repos = self._repos()
        for content_kind in (CONTENT_KIND_NEWS, CONTENT_KIND_ARTICLE):
            pending_entries = repos.push.get_pending_review_entries(content_kind)
            for entry in pending_entries:
                message = telegram_message_service.format_entry(entry)[:4096]
                success = await telegram_gateway_service.require_bot().send_message(message, parse_mode="HTML")
                repos.push.log_push_status(entry["id"], "telegram", "success" if success else "failed", None if success else "send failed")
                if success:
                    sent_ids.append(entry["id"])
        repos.review.mark_delivered(sent_ids)

    async def test_telegram_push(self) -> Dict:
        return await telegram_gateway_service.send_test_message()

    async def send_news_to_telegram(self, entry_ids: List[int]) -> Dict:
        if not entry_ids:
            raise ValidationError("请选择要发送的内容")

        repos = self._repos()
        entries = repos.review_delivery.get_entries_by_ids(entry_ids)
        if not entries:
            raise ValidationError("未找到要发送的内容")

        messages = [telegram_message_service.format_entry(entry) for entry in entries]
        await telegram_gateway_service.send_or_raise(
            "\n\n".join(messages)[:4096],
            "发送到 Telegram 失败，请检查 Bot 配置和网络连接",
        )
        repos.review.mark_delivered(entry_ids)
        return {"sent_count": len(entries), "delivery_status": DELIVERY_STATUS_SENT}


telegram_delivery_service = TelegramDeliveryService()
