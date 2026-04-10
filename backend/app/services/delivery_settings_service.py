from __future__ import annotations

from datetime import datetime

from shared.content_contract import delivery_key
from ..core.exceptions import ValidationError
from ..infrastructure.repositories import repositories


class DeliverySettingsService:
    @staticmethod
    def _repo():
        return repositories().config

    def get_schedule(self) -> dict:
        return {
            "news_time": self._repo().get_config(delivery_key("news", "time")) or "20:00",
            "article_time": self._repo().get_config(delivery_key("article", "time")) or "21:00",
        }

    def set_schedule(self, news_time: str | None, article_time: str | None) -> dict:
        try:
            repo = self._repo()
            if news_time:
                datetime.strptime(news_time, "%H:%M")
                repo.set_config(delivery_key("news", "time"), news_time)
            if article_time:
                datetime.strptime(article_time, "%H:%M")
                repo.set_config(delivery_key("article", "time"), article_time)
            return {"status": "success", "message": "Push time(s) updated successfully"}
        except ValueError as exc:
            raise ValidationError("时间格式无效，请使用 HH:MM") from exc


delivery_settings_service = DeliverySettingsService()
