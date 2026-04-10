from __future__ import annotations

import asyncio
from datetime import datetime
from logging import getLogger
from typing import Dict

from ..infrastructure.repositories import repositories
from .scraper_runtime_state_service import scraper_runtime_state_service

logger = getLogger("uvicorn")


class ScraperRunService:
    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}

    @staticmethod
    def _repos():
        return repositories()

    def is_running(self, name: str) -> bool:
        task = self._running_tasks.get(name)
        return bool(task and not task.done())

    def launch_scraper(self, name: str, items: int) -> bool:
        scraper_runtime_state_service.ensure_runtime_initialized()
        scraper_runtime_state_service.require_scraper(name)
        if self.is_running(name):
            return False
        scraper_runtime_state_service.set_scraper_state(
            name,
            {
                "status": "queued",
                "queued_at": datetime.now().isoformat(),
                "items_scraped": 0,
            },
        )
        self._running_tasks[name] = asyncio.create_task(self.run_scraper_task(name, items))
        return True

    def cancel_running_scraper(self, name: str) -> bool:
        task = self._running_tasks.get(name)
        if not task or task.done():
            return False
        task.cancel()
        return True

    async def run_scraper_task(self, name: str, max_items: int) -> None:
        logger.info(f"Starting background scrape task for {name}")
        scraper_runtime_state_service.set_scraper_state(
            name,
            {"status": "running", "start_time": datetime.now().isoformat(), "items_scraped": 0},
        )

        scraper = None
        try:
            definition = scraper_runtime_state_service.require_scraper(name)
            scraper = definition.build_scraper()
            scraper.max_items = max_items
            scraper_runtime_state_service.append_log(name, f"Initialized scraper with limit {max_items}")

            repos = self._repos()
            recent_urls = repos.news_runtime.get_recent_news_urls(scraper.site_name, limit=200)
            if recent_urls:
                scraper.existing_urls = set(recent_urls)
                scraper.last_news_url = recent_urls[0]
                scraper.incremental_mode = True
            else:
                latest_url = repos.news_runtime.get_latest_news_url(scraper.site_name)
                if latest_url:
                    scraper.last_news_url = latest_url
                    scraper.incremental_mode = True

            scraper_runtime_state_service.append_log(name, "Starting scrape...")
            news_list = await scraper.run()
            saved_count = 0
            for news in news_list:
                if "source_site" not in news:
                    news["source_site"] = scraper.site_name
                if repos.news.insert_news(news):
                    saved_count += 1

            scraper_runtime_state_service.set_scraper_state(
                name,
                {
                    "status": "idle",
                    "queued_at": None,
                    "start_time": None,
                    "last_run": datetime.now().isoformat(),
                    "last_result": f"Scraped {len(news_list)}, Saved {saved_count}",
                    "last_error": None,
                },
            )
        except asyncio.CancelledError:
            scraper_runtime_state_service.set_scraper_state(
                name,
                {
                    "status": "idle",
                    "queued_at": None,
                    "start_time": None,
                    "last_result": "Cancelled by User",
                },
            )
        except Exception as exc:
            scraper_runtime_state_service.set_scraper_state(
                name,
                {
                    "status": "error",
                    "queued_at": None,
                    "start_time": None,
                    "last_run": datetime.now().isoformat(),
                    "last_result": "Failed",
                    "last_error": str(exc),
                },
            )
        finally:
            self._running_tasks.pop(name, None)
            try:
                if scraper:
                    await scraper.close_browser()
            except Exception:
                pass

    async def wait_for_scrapers(self, timeout: int = 300) -> None:
        import time

        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                return
            running_scrapers = [
                name
                for name, status in scraper_runtime_state_service.get_spider_status().items()
                if status.get("status") in {"queued", "running"}
            ]
            if not running_scrapers:
                return
            await asyncio.sleep(10)


scraper_run_service = ScraperRunService()
