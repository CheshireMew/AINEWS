from __future__ import annotations

import asyncio
from logging import getLogger

from backend.app.services.content_lifecycle_service import content_lifecycle_service
from backend.app.services.scraper_schedule_service import scraper_schedule_service
from backend.app.services.system_settings_service import system_settings_service

logger = getLogger("uvicorn")


class AutomationRuntimeService:
    def is_working_hours(self) -> bool:
        now_hour = system_settings_service.get_system_time().hour
        return 8 <= now_hour < 24

    async def scheduler_loop(self):
        await scraper_schedule_service.scheduler_loop(self.is_working_hours)

    async def auto_pipeline_loop(self):
        logger.info("[Auto-Pipeline] Automated pipeline system started")
        await asyncio.sleep(10)
        while True:
            try:
                if not self.is_working_hours():
                    await asyncio.sleep(1800)
                    continue
                await content_lifecycle_service.run_automation_cycle()
            except Exception as exc:
                logger.error(f"[Auto-Pipeline] Error in pipeline: {exc}", exc_info=True)
            await asyncio.sleep(3600)


automation_runtime_service = AutomationRuntimeService()
