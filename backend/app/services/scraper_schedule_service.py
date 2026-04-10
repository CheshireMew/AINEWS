from __future__ import annotations

import asyncio
import random
from datetime import datetime
from logging import getLogger

from ..infrastructure.repositories import repositories
from .scraper_registry_service import scraper_registry_service
from .scraper_run_service import scraper_run_service
from .scraper_runtime_state_service import scraper_runtime_state_service

logger = getLogger("uvicorn")


class ScraperScheduleService:
    @staticmethod
    def _repos():
        return repositories()

    async def scheduler_loop(self, is_working_hours) -> None:
        scraper_runtime_state_service.ensure_runtime_initialized()
        logger.info("Starting Scheduler Loop")
        while True:
            try:
                if not is_working_hours():
                    await asyncio.sleep(1800)
                    continue

                now = datetime.now()
                repos = self._repos()
                for name in scraper_registry_service.names():
                    config = scraper_runtime_state_service.get_scraper_config(name)
                    interval = config.get("interval")
                    if not interval:
                        continue

                    status = scraper_runtime_state_service.get_scraper_state(name)
                    if status.get("status") in {"queued", "running"} or repos.scraper_commands.has_pending_command(name, "run"):
                        continue

                    last_run_str = status.get("last_run")
                    should_run = False
                    if not last_run_str:
                        should_run = True
                    else:
                        last_run = datetime.fromisoformat(last_run_str)
                        diff = (now - last_run).total_seconds() / 60
                        adjusted_interval = interval + interval * random.uniform(-0.2, 0.2)
                        if diff >= adjusted_interval:
                            should_run = True

                    if should_run:
                        definition = scraper_registry_service.get(name)
                        limit = config.get("limit", definition.default_limit if definition else 5)
                        scraper_run_service.launch_scraper(name, limit)

                await asyncio.sleep(60)
            except Exception as exc:
                logger.error(f"Scheduler Error: {exc}", exc_info=True)
                await asyncio.sleep(60)


scraper_schedule_service = ScraperScheduleService()
