from __future__ import annotations

import sqlite3

from shared.content_contract import (
    ARCHIVE_STATUS_READY,
    ARCHIVE_TABLE,
    DELIVERY_STATUS_PENDING,
    INCOMING_STAGE,
    REVIEW_STATUS_PENDING,
    REVIEW_TABLE,
)

from .sqlite_support import ensure_column


def create_news_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            source_site TEXT NOT NULL,
            source_url TEXT UNIQUE NOT NULL,
            published_at TIMESTAMP NOT NULL,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_marked_important BOOLEAN DEFAULT FALSE,
            site_importance_flag TEXT,
            stage TEXT DEFAULT '{INCOMING_STAGE}',
            keyword_filter_passed BOOLEAN,
            keyword_filter_reason TEXT,
            ai_tags TEXT,
            ai_category TEXT,
            ai_score INTEGER,
            ai_summary TEXT,
            is_duplicate BOOLEAN DEFAULT FALSE,
            duplicate_of INTEGER,
            push_status TEXT DEFAULT '{DELIVERY_STATUS_PENDING}',
            pushed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            type TEXT DEFAULT 'news',
            is_local_duplicate BOOLEAN DEFAULT FALSE,
            author TEXT DEFAULT ''
        )
        """
    )


def ensure_news_columns(cursor: sqlite3.Cursor) -> None:
    ensure_column(cursor, "news", "type", "TEXT DEFAULT 'news'")
    ensure_column(cursor, "news", "is_local_duplicate", "BOOLEAN DEFAULT FALSE")
    ensure_column(cursor, "news", "author", "TEXT DEFAULT ''")


def create_shared_tables(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS news_tags (
            news_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (news_id, tag_id),
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS processing_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER,
            stage TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS push_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER,
            platform TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS filter_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_type TEXT NOT NULL,
            rule_pattern TEXT NOT NULL,
            hit_count INTEGER DEFAULT 0,
            last_hit_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            enabled BOOLEAN DEFAULT 1,
            last_used_at TIMESTAMP,
            notes TEXT
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_enabled ON api_keys(enabled)")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scraper_runtime_state (
            scraper_name TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'idle',
            queued_at TIMESTAMP,
            start_time TIMESTAMP,
            last_run TIMESTAMP,
            last_result TEXT,
            last_error TEXT,
            items_scraped INTEGER DEFAULT 0,
            logs TEXT DEFAULT '[]',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scraper_runtime_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper_name TEXT NOT NULL,
            command_type TEXT NOT NULL,
            payload TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            result_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_scraper_runtime_commands_status ON scraper_runtime_commands(status, created_at)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_scraper_runtime_commands_scraper ON scraper_runtime_commands(scraper_name, status, created_at)"
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rss_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            feed_url TEXT NOT NULL UNIQUE,
            site_url TEXT NOT NULL,
            content_kind TEXT NOT NULL DEFAULT 'article',
            parser_type TEXT NOT NULL DEFAULT 'generic',
            default_limit INTEGER NOT NULL DEFAULT 20,
            default_interval INTEGER NOT NULL DEFAULT 240,
            enabled BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rss_sources_enabled ON rss_sources(enabled, content_kind)")


def create_archive_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {ARCHIVE_TABLE} (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            source_site TEXT NOT NULL,
            source_url TEXT NOT NULL UNIQUE,
            published_at DATETIME NOT NULL,
            scraped_at DATETIME NOT NULL,
            archived_at DATETIME NOT NULL,
            is_marked_important BOOLEAN,
            site_importance_flag TEXT,
            archive_status TEXT DEFAULT '{ARCHIVE_STATUS_READY}',
            content_type TEXT DEFAULT 'news',
            source_item_id INTEGER,
            restored_from_blocklist BOOLEAN DEFAULT FALSE,
            block_reason TEXT
        )
        """
    )
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_archive_source ON {ARCHIVE_TABLE}(source_site)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_archive_time ON {ARCHIVE_TABLE}(archived_at)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_archive_status ON {ARCHIVE_TABLE}(archive_status)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_archive_kind ON {ARCHIVE_TABLE}(content_type, archive_status, published_at)")


def create_review_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {REVIEW_TABLE} (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            source_site TEXT NOT NULL,
            source_url TEXT NOT NULL UNIQUE,
            published_at DATETIME NOT NULL,
            scraped_at DATETIME NOT NULL,
            archived_at DATETIME NOT NULL,
            queued_at DATETIME NOT NULL,
            is_marked_important BOOLEAN,
            site_importance_flag TEXT,
            content_type TEXT DEFAULT 'news',
            source_item_id INTEGER,
            review_status TEXT DEFAULT '{REVIEW_STATUS_PENDING}',
            review_summary TEXT,
            review_reason TEXT,
            review_score INTEGER,
            review_category TEXT,
            review_tags TEXT,
            delivery_status TEXT DEFAULT '{DELIVERY_STATUS_PENDING}',
            delivered_at TIMESTAMP
        )
        """
    )
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_review_source ON {REVIEW_TABLE}(source_site)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_review_queue ON {REVIEW_TABLE}(review_status)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_review_delivery ON {REVIEW_TABLE}(delivery_status)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_review_public ON {REVIEW_TABLE}(content_type, review_status, delivery_status, published_at)")


def create_daily_reports_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            news_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, type)
        )
        """
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(date DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_reports_type ON daily_reports(type)")


def create_keyword_blacklist_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS keyword_blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            match_type TEXT DEFAULT 'contains',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            type TEXT DEFAULT 'news'
        )
        """
    )
    ensure_column(cursor, "keyword_blacklist", "type", "TEXT DEFAULT 'news'")


def seed_tags(cursor: sqlite3.Cursor) -> None:
    predefined_tags = [
        ("BTC", "cryptocurrency"),
        ("ETH", "cryptocurrency"),
        ("DeFi", "topic"),
        ("NFT", "topic"),
        ("Layer2", "technology"),
        ("监管", "topic"),
        ("融资", "event"),
        ("黑客", "security"),
    ]
    for tag_name, category in predefined_tags:
        cursor.execute("INSERT OR IGNORE INTO tags (name, category) VALUES (?, ?)", (tag_name, category))
