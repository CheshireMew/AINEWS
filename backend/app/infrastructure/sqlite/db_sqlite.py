"""SQLite 数据库实现。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from shared.db_base import DatabaseBase

from .sqlite_migrations import (
    migrate_archive_table,
    migrate_legacy_config,
    migrate_review_table,
    normalize_news_stages,
    seed_default_rss_sources,
)
from .sqlite_schema import (
    create_archive_table,
    create_daily_reports_table,
    create_keyword_blacklist_table,
    create_news_table,
    create_review_table,
    create_shared_tables,
    ensure_news_columns,
    seed_tags,
)


class Database(DatabaseBase):
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = str(Path(__file__).resolve().parents[4] / "ainews.db")
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False, isolation_level=None)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass

        cursor = conn.cursor()
        try:
            create_news_table(cursor)
            ensure_news_columns(cursor)
            create_shared_tables(cursor)
            create_archive_table(cursor)
            create_review_table(cursor)
            create_daily_reports_table(cursor)
            create_keyword_blacklist_table(cursor)
            migrate_archive_table(cursor)
            migrate_review_table(cursor)
            normalize_news_stages(cursor)
            migrate_legacy_config(cursor)
            seed_default_rss_sources(cursor)
            seed_tags(cursor)
            conn.commit()
        finally:
            conn.close()
