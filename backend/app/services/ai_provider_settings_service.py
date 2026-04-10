from __future__ import annotations

from shared.content_contract import integration_key
from ..infrastructure.repositories import repositories


class AIProviderSettingsService:
    @staticmethod
    def _repo():
        return repositories().config

    def get_config(self) -> dict:
        return {
            "api_key": self._repo().get_config(integration_key("llm", "api_key")) or "",
            "base_url": self._repo().get_config(integration_key("llm", "base_url")) or "https://api.deepseek.com",
            "model": self._repo().get_config(integration_key("llm", "model")) or "deepseek-chat",
        }

    def set_config(self, config: dict) -> dict:
        repo = self._repo()
        repo.set_config(integration_key("llm", "api_key"), config["api_key"])
        repo.set_config(integration_key("llm", "base_url"), config["base_url"])
        repo.set_config(integration_key("llm", "model"), config["model"])
        return {"message": "配置已保存"}


ai_provider_settings_service = AIProviderSettingsService()
