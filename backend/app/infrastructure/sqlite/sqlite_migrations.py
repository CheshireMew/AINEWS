from __future__ import annotations

import sqlite3

from shared.content_contract import (
    ARCHIVE_STATUS_BLOCKED,
    ARCHIVE_STATUS_READY,
    ARCHIVE_STATUS_REVIEWED,
    ARCHIVED_STAGE,
    DELIVERY_STATUS_PENDING,
    DEDUP_THRESHOLD_KEY,
    INCOMING_STAGE,
    REVIEW_STATUS_DISCARDED,
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_SELECTED,
    SYSTEM_TIMEZONE_KEY,
    automation_key,
    delivery_key,
    integration_key,
    review_key,
    ARCHIVE_TABLE,
    REVIEW_TABLE,
)

from .sqlite_support import table_exists


LEGACY_CONFIG_GROUPS = {
    SYSTEM_TIMEZONE_KEY: ["system_timezone"],
    delivery_key("news", "time"): ["daily_push_time"],
    delivery_key("article", "time"): ["daily_article_push_time"],
    delivery_key("news", "last_date"): ["last_daily_push_date"],
    delivery_key("article", "last_date"): ["last_daily_article_push_date"],
    automation_key("news", "scan_hours"): ["news_dedup_hours", "auto_dedup_hours"],
    automation_key("news", "window_hours"): ["news_dedup_window_hours"],
    automation_key("news", "block_hours"): ["news_filter_hours", "auto_filter_hours"],
    automation_key("news", "review_hours"): ["news_ai_scoring_hours", "auto_ai_scoring_hours"],
    automation_key("news", "delivery_hours"): ["news_push_hours", "auto_push_hours"],
    automation_key("article", "scan_hours"): ["article_dedup_hours", "auto_article_dedup_hours", "article_auto_dedup_hours"],
    automation_key("article", "window_hours"): ["article_dedup_window_hours"],
    automation_key("article", "block_hours"): ["article_filter_hours", "auto_article_filter_hours", "article_auto_filter_hours"],
    automation_key("article", "review_hours"): ["article_ai_scoring_hours", "auto_article_ai_scoring_hours", "article_auto_ai_scoring_hours"],
    automation_key("article", "delivery_hours"): ["article_push_hours", "auto_article_push_hours", "article_auto_push_hours"],
    review_key("news", "prompt"): ["ai_filter_prompt_news", "ai_filter_prompt"],
    review_key("article", "prompt"): ["ai_filter_prompt_article", "ai_filter_prompt"],
    review_key("news", "hours"): ["ai_filter_hours_news", "ai_filter_hours"],
    review_key("article", "hours"): ["ai_filter_hours_article", "ai_filter_hours"],
    integration_key("llm", "api_key"): ["llm_api_key"],
    integration_key("llm", "base_url"): ["llm_base_url"],
    integration_key("llm", "model"): ["llm_model"],
    integration_key("telegram", "bot_token"): ["telegram_bot_token"],
    integration_key("telegram", "chat_id"): ["telegram_chat_id"],
    integration_key("telegram", "enabled"): ["telegram_enabled"],
    DEDUP_THRESHOLD_KEY: ["dedup_threshold"],
}

LEGACY_CONFIG_KEYS = {key for keys in LEGACY_CONFIG_GROUPS.values() for key in keys}


def migrate_archive_table(cursor: sqlite3.Cursor) -> None:
    if not table_exists(cursor, "deduplicated_news"):
        return
    cursor.execute(
        f"""
        INSERT OR IGNORE INTO {ARCHIVE_TABLE} (
            id, title, content, source_site, source_url, published_at, scraped_at, archived_at,
            is_marked_important, site_importance_flag, archive_status, content_type, source_item_id,
            restored_from_blocklist, block_reason
        )
        SELECT
            id,
            title,
            content,
            source_site,
            source_url,
            published_at,
            scraped_at,
            deduplicated_at,
            is_marked_important,
            site_importance_flag,
            CASE stage
                WHEN 'filtered' THEN '{ARCHIVE_STATUS_BLOCKED}'
                WHEN 'verified' THEN '{ARCHIVE_STATUS_REVIEWED}'
                ELSE '{ARCHIVE_STATUS_READY}'
            END,
            COALESCE(type, 'news'),
            original_news_id,
            COALESCE(is_whitelist_restored, 0),
            keyword_filter_reason
        FROM deduplicated_news
        """
    )
    cursor.execute("DROP TABLE deduplicated_news")


def migrate_review_table(cursor: sqlite3.Cursor) -> None:
    if not table_exists(cursor, "curated_news"):
        return
    cursor.execute(
        f"""
        INSERT OR IGNORE INTO {REVIEW_TABLE} (
            id, title, content, source_site, source_url, published_at, scraped_at, archived_at, queued_at,
            is_marked_important, site_importance_flag, content_type, source_item_id, review_status,
            review_summary, review_reason, review_score, review_category, review_tags, delivery_status, delivered_at
        )
        SELECT
            id,
            title,
            content,
            source_site,
            source_url,
            published_at,
            scraped_at,
            deduplicated_at,
            curated_at,
            is_marked_important,
            site_importance_flag,
            COALESCE(type, 'news'),
            original_news_id,
            CASE
                WHEN ai_status = 'approved' THEN '{REVIEW_STATUS_SELECTED}'
                WHEN ai_status = 'rejected' THEN '{REVIEW_STATUS_DISCARDED}'
                ELSE '{REVIEW_STATUS_PENDING}'
            END,
            ai_summary,
            ai_explanation,
            ai_score,
            ai_category,
            ai_tags,
            COALESCE(push_status, '{DELIVERY_STATUS_PENDING}'),
            pushed_at
        FROM curated_news
        """
    )
    cursor.execute("DROP TABLE curated_news")


def normalize_news_stages(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        f"""
        UPDATE news
        SET stage = CASE stage
            WHEN 'raw' THEN '{INCOMING_STAGE}'
            WHEN 'deduplicated' THEN '{ARCHIVED_STAGE}'
            WHEN 'verified' THEN '{ARCHIVED_STAGE}'
            WHEN 'filtered' THEN '{ARCHIVED_STAGE}'
            ELSE COALESCE(stage, '{INCOMING_STAGE}')
        END
        """
    )


def migrate_legacy_config(cursor: sqlite3.Cursor) -> None:
    cursor.execute("SELECT key, value FROM system_config")
    existing = {row["key"]: row["value"] for row in cursor.fetchall()}

    for canonical_key, legacy_keys in LEGACY_CONFIG_GROUPS.items():
        if existing.get(canonical_key):
            continue
        for legacy_key in legacy_keys:
            legacy_value = existing.get(legacy_key)
            if legacy_value not in (None, ""):
                cursor.execute(
                    """
                    INSERT INTO system_config (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at
                    """,
                    (canonical_key, legacy_value),
                )
                existing[canonical_key] = legacy_value
                break

    if SYSTEM_TIMEZONE_KEY not in existing:
        cursor.execute(
            """
            INSERT INTO system_config (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO NOTHING
            """,
            (SYSTEM_TIMEZONE_KEY, "Asia/Shanghai"),
        )

    for legacy_key in LEGACY_CONFIG_KEYS:
        cursor.execute("DELETE FROM system_config WHERE key = ?", (legacy_key,))


def seed_default_rss_sources(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """
        INSERT INTO rss_sources (
            slug, display_name, feed_url, site_url, content_kind, parser_type,
            default_limit, default_interval, enabled, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(slug) DO UPDATE SET
            display_name = excluded.display_name,
            feed_url = excluded.feed_url,
            site_url = excluded.site_url,
            content_kind = excluded.content_kind,
            parser_type = excluded.parser_type,
            default_limit = excluded.default_limit,
            default_interval = excluded.default_interval,
            enabled = excluded.enabled,
            updated_at = excluded.updated_at
        """,
        (
            "chainfeeds",
            "Chainfeeds Article",
            "https://www.chainfeeds.me/rss",
            "https://www.chainfeeds.xyz",
            "article",
            "summary_source_link",
            20,
            240,
            1,
        ),
    )
