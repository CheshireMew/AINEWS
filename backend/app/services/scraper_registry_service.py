from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..core.exceptions import NotFoundError
from ..infrastructure.scraper_impl.rss_feed import RssFeedScraper
from ..infrastructure.scrapers import scraper_catalog
from .rss_source_service import rss_runtime_name, rss_source_service


@dataclass(frozen=True)
class RegisteredScraper:
    name: str
    display_name: str
    source_site: str
    content_kind: str
    default_limit: int
    default_interval: int
    source_type: str
    build_scraper: Callable[[], object]


class ScraperRegistryService:
    def list_definitions(self) -> list[RegisteredScraper]:
        definitions = [
            RegisteredScraper(
                name=definition.name,
                display_name=definition.display_name(),
                source_site=definition.source_site(),
                content_kind=definition.content_kind,
                default_limit=definition.default_limit,
                default_interval=definition.default_interval,
                source_type="site",
                build_scraper=definition.scraper_cls,
            )
            for definition in scraper_catalog.definitions()
        ]

        for source in rss_source_service.list_enabled_sources():
            definitions.append(
                RegisteredScraper(
                    name=rss_runtime_name(source["slug"]),
                    display_name=source["display_name"],
                    source_site=source["display_name"],
                    content_kind=source["content_kind"],
                    default_limit=source["default_limit"],
                    default_interval=source["default_interval"],
                    source_type="rss",
                    build_scraper=lambda source=source: RssFeedScraper(source),
                )
            )

        return definitions

    def names(self) -> list[str]:
        return [definition.name for definition in self.list_definitions()]

    def get(self, name: str) -> RegisteredScraper | None:
        for definition in self.list_definitions():
            if definition.name == name:
                return definition
        return None

    def require(self, name: str) -> RegisteredScraper:
        definition = self.get(name)
        if not definition:
            raise NotFoundError("爬虫不存在")
        return definition


scraper_registry_service = ScraperRegistryService()
