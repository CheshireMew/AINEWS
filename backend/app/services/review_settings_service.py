from __future__ import annotations

from shared.content_contract import review_key
from ..infrastructure.repositories import repositories


class ReviewSettingsService:
    @staticmethod
    def _repo():
        return repositories().config

    @staticmethod
    def _positive_int(value: str | None, default: int) -> int:
        try:
            return max(1, int(value or default))
        except Exception:
            return default

    def get_config(self, content_kind: str = "news") -> dict:
        repo = self._repo()
        return {
            "prompt": repo.get_config(review_key(content_kind, "prompt")) or "",
            "hours": self._positive_int(repo.get_config(review_key(content_kind, "hours")), 8),
            "kind": content_kind,
        }

    def set_config(self, prompt: str | None, hours: int | None, content_kind: str = "news") -> dict:
        repo = self._repo()
        if prompt is not None:
            repo.set_config(review_key(content_kind, "prompt"), prompt)
        if hours is not None:
            repo.set_config(review_key(content_kind, "hours"), str(hours))
        return {"message": "配置已保存"}


review_settings_service = ReviewSettingsService()
