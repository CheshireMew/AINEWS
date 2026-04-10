from __future__ import annotations

import asyncio
from logging import getLogger

from backend.app.infrastructure.database import init_database
from backend.app.services.automation_runtime_service import automation_runtime_service
from backend.app.services.scraper_command_service import scraper_command_service
from backend.app.services.scraper_runtime_state_service import scraper_runtime_state_service

logger = getLogger("uvicorn")


async def main():
    init_database()
    scraper_runtime_state_service.ensure_runtime_initialized()
    logger.info("Database initialized")
    tasks = [
        asyncio.create_task(scraper_command_service.command_loop(), name="scraper_command_loop"),
        asyncio.create_task(automation_runtime_service.scheduler_loop(), name="scheduler_loop"),
        asyncio.create_task(automation_runtime_service.auto_pipeline_loop(), name="auto_pipeline_loop"),
    ]
    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
