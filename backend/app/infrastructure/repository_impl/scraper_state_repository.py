from __future__ import annotations

import json
from datetime import datetime
from typing import Dict

from .base_repository import BaseRepository


class ScraperStateRepository(BaseRepository):
    def ensure_state(self, scraper_name: str) -> None:
        self.execute(
            """
            INSERT INTO scraper_runtime_state (scraper_name, status, logs, updated_at)
            VALUES (?, 'idle', '[]', CURRENT_TIMESTAMP)
            ON CONFLICT(scraper_name) DO NOTHING
            """,
            (scraper_name,),
        )

    def get_state(self, scraper_name: str) -> Dict:
        cursor = self.execute(
            """
            SELECT scraper_name, status, queued_at, start_time, last_run, last_result,
                   last_error, items_scraped, logs, updated_at
            FROM scraper_runtime_state
            WHERE scraper_name = ?
            """,
            (scraper_name,),
        )
        row = cursor.fetchone()
        return self._normalize_state(dict(row) if row else {"scraper_name": scraper_name})

    def list_states(self) -> Dict[str, Dict]:
        cursor = self.execute(
            """
            SELECT scraper_name, status, queued_at, start_time, last_run, last_result,
                   last_error, items_scraped, logs, updated_at
            FROM scraper_runtime_state
            """
        )
        return {row["scraper_name"]: self._normalize_state(dict(row)) for row in cursor.fetchall()}

    def update_state(self, scraper_name: str, payload: Dict) -> Dict:
        current = self.get_state(scraper_name)
        state = {**current, **payload, "scraper_name": scraper_name}
        logs = state.get("logs", [])
        state["logs"] = logs if isinstance(logs, list) else []
        self.execute(
            """
            INSERT INTO scraper_runtime_state (
                scraper_name, status, queued_at, start_time, last_run, last_result,
                last_error, items_scraped, logs, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(scraper_name) DO UPDATE SET
                status = excluded.status,
                queued_at = excluded.queued_at,
                start_time = excluded.start_time,
                last_run = excluded.last_run,
                last_result = excluded.last_result,
                last_error = excluded.last_error,
                items_scraped = excluded.items_scraped,
                logs = excluded.logs,
                updated_at = excluded.updated_at
            """,
            (
                scraper_name,
                state.get("status", "idle"),
                state.get("queued_at"),
                state.get("start_time"),
                state.get("last_run"),
                state.get("last_result"),
                state.get("last_error"),
                state.get("items_scraped", 0),
                json.dumps(state["logs"], ensure_ascii=False),
            ),
        )
        return state

    def append_log(self, scraper_name: str, message: str) -> Dict:
        current = self.get_state(scraper_name)
        logs = current.get("logs", [])
        full_message = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        logs.append(full_message)
        current["logs"] = logs[-100:]
        return self.update_state(scraper_name, current)

    def delete_state(self, scraper_name: str) -> None:
        self.execute("DELETE FROM scraper_runtime_state WHERE scraper_name = ?", (scraper_name,))

    @staticmethod
    def _normalize_state(state: Dict) -> Dict:
        logs = state.get("logs")
        if isinstance(logs, str):
            try:
                state["logs"] = json.loads(logs)
            except Exception:
                state["logs"] = []
        elif not isinstance(logs, list):
            state["logs"] = []
        state.setdefault("status", "idle")
        state.setdefault("items_scraped", 0)
        return state
