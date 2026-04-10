from __future__ import annotations

import asyncio
from datetime import datetime
from logging import getLogger
from typing import Dict

from ..infrastructure.repositories import repositories, transactional_repositories
from .scraper_run_service import scraper_run_service
from .scraper_runtime_state_service import scraper_runtime_state_service

logger = getLogger("uvicorn")


class ScraperCommandService:
    @staticmethod
    def _repos():
        return repositories()

    async def request_run(self, name: str, items: int) -> Dict:
        with transactional_repositories() as tx_repos:
            scraper_runtime_state_service.ensure_runtime_initialized()
            scraper_runtime_state_service.require_scraper(name)
            state = scraper_runtime_state_service.get_scraper_state(name)
            if state.get("status") in {"queued", "running"} or tx_repos.scraper_commands.has_pending_command(name, "run"):
                return {"status": "accepted", "message": f"Scraper {name} already queued"}
            tx_repos.scraper_commands.enqueue_command(name, "run", {"items": items})
            scraper_runtime_state_service.set_scraper_state(
                name,
                {"status": "queued", "queued_at": datetime.now().isoformat(), "items_scraped": 0},
            )
            scraper_runtime_state_service.append_log(name, f"Run requested with limit {items}")
            logger.info(f"Queued run request for {name}")
            return {"status": "accepted", "message": f"Scraper {name} queued"}

    async def request_stop(self, name: str) -> Dict:
        with transactional_repositories() as tx_repos:
            scraper_runtime_state_service.ensure_runtime_initialized()
            scraper_runtime_state_service.require_scraper(name)
            state = scraper_runtime_state_service.get_scraper_state(name)
            if tx_repos.scraper_commands.has_pending_command(name, "stop"):
                return {"status": "accepted", "message": f"Stop already requested for {name}"}
            if state.get("status") not in {"queued", "running"} and not tx_repos.scraper_commands.has_pending_command(name, "run"):
                return {"status": "error", "message": "Scraper not running"}
            tx_repos.scraper_commands.enqueue_command(name, "stop")
            scraper_runtime_state_service.append_log(name, "Stop requested")
            logger.info(f"Queued stop request for {name}")
            return {"status": "accepted", "message": f"Stop signal queued for {name}"}

    async def command_loop(self) -> None:
        scraper_runtime_state_service.ensure_runtime_initialized()
        logger.info("Starting Scraper Command Loop")
        while True:
            try:
                command = self._repos().scraper_commands.claim_next_command()
                if not command:
                    await asyncio.sleep(1)
                    continue
                await self._handle_command(command)
            except Exception as exc:
                logger.error(f"Scraper command loop error: {exc}", exc_info=True)
                await asyncio.sleep(1)

    async def _handle_command(self, command: Dict) -> None:
        scraper_name = command["scraper_name"]
        command_id = command["id"]
        command_type = command["command_type"]
        try:
            with transactional_repositories() as tx_repos:
                if command_type == "run":
                    if not scraper_run_service.is_running(scraper_name):
                        items = int(
                            command.get("payload", {}).get("items")
                            or scraper_runtime_state_service.get_scraper_config(scraper_name).get("limit", 5)
                        )
                        scraper_run_service.launch_scraper(scraper_name, items)
                    tx_repos.scraper_commands.complete_command(command_id, "Run request accepted")
                    return

                if command_type == "stop":
                    cancelled = tx_repos.scraper_commands.cancel_pending_run_commands(scraper_name)
                    if scraper_run_service.cancel_running_scraper(scraper_name):
                        tx_repos.scraper_commands.complete_command(command_id, "Running scraper cancelled")
                    elif cancelled:
                        scraper_runtime_state_service.set_scraper_state(
                            scraper_name,
                            {"status": "idle", "queued_at": None, "start_time": None, "last_result": "Cancelled before start"},
                        )
                        scraper_runtime_state_service.append_log(scraper_name, "Pending run cancelled")
                        tx_repos.scraper_commands.complete_command(command_id, "Pending run cancelled")
                    else:
                        tx_repos.scraper_commands.complete_command(command_id, "Scraper already idle")
                    return

                tx_repos.scraper_commands.fail_command(command_id, f"Unknown command: {command_type}")
        except Exception as exc:
            with transactional_repositories() as tx_repos:
                tx_repos.scraper_commands.fail_command(command_id, str(exc))
            raise


scraper_command_service = ScraperCommandService()
