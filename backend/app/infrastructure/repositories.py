from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import sqlite3

from .repository_impl.api_key_repository import ApiKeyRepository
from .repository_impl.archive_repository import ArchiveRepository
from .repository_impl.archive_query_repository import ArchiveQueryRepository
from .repository_impl.blacklist_repository import BlacklistRepository
from .repository_impl.config_repository import ConfigRepository
from .repository_impl.daily_report_repository import DailyReportRepository
from .repository_impl.news_admin_repository import NewsAdminRepository
from .repository_impl.news_repository import NewsRepository
from .repository_impl.news_runtime_repository import NewsRuntimeRepository
from .repository_impl.news_source_group_repository import NewsSourceGroupRepository
from .repository_impl.push_repository import PushRepository
from .repository_impl.rss_source_repository import RssSourceRepository
from .repository_impl.review_admin_repository import ReviewAdminRepository
from .repository_impl.review_delivery_repository import ReviewDeliveryRepository
from .repository_impl.review_public_repository import ReviewPublicRepository
from .repository_impl.review_repository import ReviewRepository
from .repository_impl.scraper_command_repository import ScraperCommandRepository
from .repository_impl.scraper_state_repository import ScraperStateRepository

from .database import database


class AppRepositories:
    def __init__(self, conn: sqlite3.Connection | None = None):
        source = conn or database
        self.config = ConfigRepository(source)
        self.news = NewsRepository(source)
        self.news_admin = NewsAdminRepository(source)
        self.news_runtime = NewsRuntimeRepository(source)
        self.news_source_groups = NewsSourceGroupRepository(source)
        self.archive = ArchiveRepository(source)
        self.archive_query = ArchiveQueryRepository(source)
        self.review = ReviewRepository(source)
        self.review_admin = ReviewAdminRepository(source)
        self.review_delivery = ReviewDeliveryRepository(source)
        self.review_public = ReviewPublicRepository(source)
        self.blacklist = BlacklistRepository(source)
        self.api_keys = ApiKeyRepository(source)
        self.push = PushRepository(source)
        self.daily_reports = DailyReportRepository(source)
        self.scraper_state = ScraperStateRepository(source)
        self.scraper_commands = ScraperCommandRepository(source)
        self.rss_sources = RssSourceRepository(source)


_current_repositories: ContextVar[AppRepositories | None] = ContextVar("current_repositories", default=None)


class RepositorySession:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.repos = AppRepositories(conn)


def repositories(conn: sqlite3.Connection | None = None) -> AppRepositories:
    if conn is not None:
        return AppRepositories(conn)
    current = _current_repositories.get()
    if current is not None:
        return current
    return AppRepositories(conn)


@contextmanager
def repository_session():
    conn = database.connect()
    token = None
    try:
        session = RepositorySession(conn)
        token = _current_repositories.set(session.repos)
        yield session
    finally:
        if token is not None:
            _current_repositories.reset(token)
        conn.close()


@contextmanager
def transactional_repositories():
    with repository_session() as session:
        try:
            session.conn.execute("BEGIN")
            yield session.repos
            session.conn.commit()
        except Exception:
            session.conn.rollback()
            raise
