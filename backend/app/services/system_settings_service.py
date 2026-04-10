from __future__ import annotations

from datetime import datetime
import zoneinfo

from shared.content_contract import SYSTEM_TIMEZONE_KEY
from ..core.exceptions import ValidationError
from ..infrastructure.repositories import repositories


class SystemSettingsService:
    @staticmethod
    def _repo():
        return repositories().config

    def get_timezone(self) -> dict:
        return {"timezone": self._repo().get_config(SYSTEM_TIMEZONE_KEY) or "Asia/Shanghai"}

    def get_system_time(self) -> datetime:
        return self._repo().get_system_time()

    def set_timezone(self, timezone: str) -> dict:
        try:
            zoneinfo.ZoneInfo(timezone)
            self._repo().set_config(SYSTEM_TIMEZONE_KEY, timezone)
            return {"status": "success", "message": f"Timezone set to {timezone}"}
        except Exception as exc:
            raise ValidationError("时区无效") from exc


system_settings_service = SystemSettingsService()
