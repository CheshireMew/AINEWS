from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _load_contract() -> dict:
    contract_path = Path(__file__).with_name("content_contract.json")
    return json.loads(contract_path.read_text(encoding="utf-8"))


_CONTRACT = _load_contract()

CONTENT_KIND_NEWS = _CONTRACT["contentKinds"]["news"]
CONTENT_KIND_ARTICLE = _CONTRACT["contentKinds"]["article"]
CONTENT_KINDS = (CONTENT_KIND_NEWS, CONTENT_KIND_ARTICLE)

INCOMING_STAGE = _CONTRACT["stages"]["incoming"]
ARCHIVED_STAGE = _CONTRACT["stages"]["archived"]
DUPLICATE_STAGE = _CONTRACT["stages"]["duplicate"]

ARCHIVE_TABLE = _CONTRACT["archive"]["table"]
ARCHIVE_STATUS_READY = _CONTRACT["archive"]["statuses"]["ready"]
ARCHIVE_STATUS_BLOCKED = _CONTRACT["archive"]["statuses"]["blocked"]
ARCHIVE_STATUS_REVIEWED = _CONTRACT["archive"]["statuses"]["reviewed"]

REVIEW_TABLE = _CONTRACT["review"]["table"]
REVIEW_STATUS_PENDING = _CONTRACT["review"]["statuses"]["pending"]
REVIEW_STATUS_SELECTED = _CONTRACT["review"]["statuses"]["selected"]
REVIEW_STATUS_DISCARDED = _CONTRACT["review"]["statuses"]["discarded"]

DELIVERY_STATUS_PENDING = _CONTRACT["delivery"]["statuses"]["pending"]
DELIVERY_STATUS_SENT = _CONTRACT["delivery"]["statuses"]["sent"]

EXPORT_SCOPE_INCOMING = _CONTRACT["exportScopes"]["incoming"]
EXPORT_SCOPE_ARCHIVE = _CONTRACT["exportScopes"]["archive"]
EXPORT_SCOPE_BLOCKED = _CONTRACT["exportScopes"]["blocked"]
EXPORT_SCOPE_REVIEW = _CONTRACT["exportScopes"]["review"]
EXPORT_SCOPE_SELECTED = _CONTRACT["exportScopes"]["selected"]
EXPORT_SCOPE_DISCARDED = _CONTRACT["exportScopes"]["discarded"]

PUBLIC_STREAM_BRIEFS = _CONTRACT["publicStreams"]["briefs"]
PUBLIC_STREAM_LONGFORM = _CONTRACT["publicStreams"]["longform"]
PUBLIC_STREAM_MAP = {
    PUBLIC_STREAM_BRIEFS: CONTENT_KIND_NEWS,
    PUBLIC_STREAM_LONGFORM: CONTENT_KIND_ARTICLE,
}

REVIEW_DECISION_MAP = {
    REVIEW_STATUS_SELECTED: REVIEW_STATUS_SELECTED,
    REVIEW_STATUS_DISCARDED: REVIEW_STATUS_DISCARDED,
}

SYSTEM_TIMEZONE_KEY = _CONTRACT["configKeys"]["systemTimezone"]
DEDUP_THRESHOLD_KEY = _CONTRACT["configKeys"]["dedupThreshold"]


def automation_key(kind: str, field: str) -> str:
    return f"automation.{kind}.{field}"


def review_key(kind: str, field: str) -> str:
    return f"review.{kind}.{field}"


def delivery_key(kind: str, field: str) -> str:
    return f"delivery.{kind}.{field}"


def integration_key(group: str, field: str) -> str:
    return f"integration.{group}.{field}"
