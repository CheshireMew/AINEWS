from __future__ import annotations

import json
from typing import Dict, Optional

from ..core.exceptions import NotFoundError
from ..infrastructure.repositories import repositories
from .scraper_registry_service import scraper_registry_service


class ScraperRuntimeStateService:
    @staticmethod
    def _repos():
        return repositories()

    @staticmethod
    def _config_key(name: str) -> str:
        return f"scraper.{name}.runtime"

    def ensure_runtime_initialized(self) -> None:
        repos = self._repos()
        for definition in scraper_registry_service.list_definitions():
            name = definition.name
            if not repos.config.get_config(self._config_key(name)):
                defaults = {"limit": definition.default_limit, "interval": definition.default_interval}
                repos.config.set_config(self._config_key(name), json.dumps(defaults, ensure_ascii=False))
            repos.scraper_state.ensure_state(name)

    def require_scraper(self, name: str):
        return scraper_registry_service.require(name)

    def get_scraper_config(self, name: str) -> Dict:
        definition = scraper_registry_service.get(name)
        defaults = {"limit": definition.default_limit, "interval": definition.default_interval} if definition else {"limit": 5, "interval": 60}
        raw = self._repos().config.get_config(self._config_key(name))
        if not raw:
            return defaults.copy()
        try:
            return {**defaults, **json.loads(raw)}
        except Exception:
            return defaults.copy()

    def update_scraper_config(self, name: str, interval: Optional[str], limit: Optional[int]) -> Dict:
        self.ensure_runtime_initialized()
        self.require_scraper(name)
        config = self.get_scraper_config(name)
        if interval is not None:
            if interval == "manual":
                config.pop("interval", None)
            else:
                config["interval"] = int(interval)
        if limit is not None:
            config["limit"] = limit
        self._repos().config.set_config(self._config_key(name), json.dumps(config, ensure_ascii=False))
        return {"status": "success", "config": config}

    def get_spiders(self) -> Dict:
        self.ensure_runtime_initialized()
        return {
            "spiders": [
                {
                    "name": definition.name,
                    "display_name": definition.display_name,
                    "source_site": definition.source_site,
                    "type": definition.content_kind,
                    "source_type": definition.source_type,
                }
                for definition in scraper_registry_service.list_definitions()
            ]
        }

    def get_scraper_state(self, name: str) -> Dict:
        self.ensure_runtime_initialized()
        self.require_scraper(name)
        return self._repos().scraper_state.get_state(name)

    def get_spider_status(self) -> Dict:
        self.ensure_runtime_initialized()
        payload = {}
        for definition in scraper_registry_service.list_definitions():
            name = definition.name
            payload[name] = {
                **self._repos().scraper_state.get_state(name),
                **self.get_scraper_config(name),
            }
        return payload

    def set_scraper_state(self, name: str, payload: Dict) -> None:
        self.ensure_runtime_initialized()
        self._repos().scraper_state.update_state(name, payload)

    def append_log(self, name: str, message: str) -> None:
        self.ensure_runtime_initialized()
        self._repos().scraper_state.append_log(name, message)


scraper_runtime_state_service = ScraperRuntimeStateService()
