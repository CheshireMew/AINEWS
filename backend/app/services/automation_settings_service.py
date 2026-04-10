from __future__ import annotations

from shared.content_contract import CONTENT_KINDS, DEDUP_THRESHOLD_KEY, automation_key
from ..core.exceptions import ValidationError
from ..infrastructure.repositories import repositories


AUTOMATION_DEFAULTS = {
    "news": {"dedup_hours": 2, "dedup_window_hours": 2, "filter_hours": 24, "ai_scoring_hours": 10, "push_hours": 12},
    "article": {"dedup_hours": 168, "dedup_window_hours": 72, "filter_hours": 168, "ai_scoring_hours": 168, "push_hours": 72},
}
AUTOMATION_FIELD_MAP = {
    "dedup_hours": "scan_hours",
    "dedup_window_hours": "window_hours",
    "filter_hours": "block_hours",
    "ai_scoring_hours": "review_hours",
    "push_hours": "delivery_hours",
}


class AutomationSettingsService:
    @staticmethod
    def _repo():
        return repositories().config

    @staticmethod
    def _positive_int(value: str | None, default: int) -> int:
        try:
            return max(1, int(value or default))
        except Exception:
            return default

    def get_config(self) -> dict:
        return {content_kind: self.get_window(content_kind) for content_kind in CONTENT_KINDS}

    def get_window(self, content_kind: str) -> dict:
        if content_kind not in CONTENT_KINDS:
            raise ValidationError("内容类型无效")
        defaults = AUTOMATION_DEFAULTS[content_kind]
        repo = self._repo()
        return {
            "dedup_hours": self._positive_int(repo.get_config(automation_key(content_kind, AUTOMATION_FIELD_MAP["dedup_hours"])), defaults["dedup_hours"]),
            "dedup_window_hours": self._positive_int(repo.get_config(automation_key(content_kind, AUTOMATION_FIELD_MAP["dedup_window_hours"])), defaults["dedup_window_hours"]),
            "filter_hours": self._positive_int(repo.get_config(automation_key(content_kind, AUTOMATION_FIELD_MAP["filter_hours"])), defaults["filter_hours"]),
            "ai_scoring_hours": self._positive_int(repo.get_config(automation_key(content_kind, AUTOMATION_FIELD_MAP["ai_scoring_hours"])), defaults["ai_scoring_hours"]),
            "push_hours": self._positive_int(repo.get_config(automation_key(content_kind, AUTOMATION_FIELD_MAP["push_hours"])), defaults["push_hours"]),
        }

    def set_config(self, config: dict) -> dict:
        repo = self._repo()
        for content_kind, values in config.items():
            if content_kind not in CONTENT_KINDS or not values:
                continue
            for key, value in values.items():
                field = AUTOMATION_FIELD_MAP.get(key)
                if field and value is not None:
                    repo.set_config(automation_key(content_kind, field), str(value))
        return {"status": "success", "message": "配置已保存"}

    def get_dedup_threshold(self) -> float:
        try:
            return float(self._repo().get_config(DEDUP_THRESHOLD_KEY) or 0.50)
        except Exception:
            return 0.50

    def set_dedup_threshold(self, threshold: float) -> None:
        self._repo().set_config(DEDUP_THRESHOLD_KEY, str(threshold))


automation_settings_service = AutomationSettingsService()
