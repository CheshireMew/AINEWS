from __future__ import annotations

from shared.content_contract import integration_key
from ..infrastructure.repositories import repositories


class TelegramSettingsService:
    @staticmethod
    def _repo():
        return repositories().config

    def get_config(self) -> dict:
        return {
            "bot_token": self._repo().get_config(integration_key("telegram", "bot_token")) or "",
            "chat_id": self._repo().get_config(integration_key("telegram", "chat_id")) or "",
            "enabled": self._repo().get_config(integration_key("telegram", "enabled")) == "true",
        }

    def set_config(self, config: dict) -> dict:
        repo = self._repo()
        repo.set_config(integration_key("telegram", "bot_token"), config["bot_token"])
        repo.set_config(integration_key("telegram", "chat_id"), config["chat_id"])
        repo.set_config(integration_key("telegram", "enabled"), "true" if config["enabled"] else "false")
        return {"message": "配置已保存"}


telegram_settings_service = TelegramSettingsService()
