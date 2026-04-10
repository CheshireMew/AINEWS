from __future__ import annotations

import json
from typing import Dict, Optional

from .base_repository import BaseRepository


class ScraperCommandRepository(BaseRepository):
    def enqueue_command(self, scraper_name: str, command_type: str, payload: Optional[Dict] = None) -> int:
        cursor = self.execute(
            """
            INSERT INTO scraper_runtime_commands (scraper_name, command_type, payload, status, updated_at)
            VALUES (?, ?, ?, 'pending', CURRENT_TIMESTAMP)
            """,
            (scraper_name, command_type, json.dumps(payload or {}, ensure_ascii=False)),
        )
        return cursor.lastrowid

    def has_pending_command(self, scraper_name: str, command_type: str) -> bool:
        cursor = self.execute(
            """
            SELECT 1
            FROM scraper_runtime_commands
            WHERE scraper_name = ? AND command_type = ? AND status IN ('pending', 'processing')
            LIMIT 1
            """,
            (scraper_name, command_type),
        )
        return cursor.fetchone() is not None

    def claim_next_command(self) -> Optional[Dict]:
        managed_conn = self.conn is None
        conn = self.conn or self.db.connect()
        cursor = conn.cursor()
        started_transaction = False
        try:
            if not conn.in_transaction:
                conn.execute("BEGIN")
                started_transaction = True
            cursor.execute(
                """
                SELECT id, scraper_name, command_type, payload, status, created_at, updated_at
                FROM scraper_runtime_commands
                WHERE status = 'pending'
                ORDER BY created_at ASC, id ASC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if not row:
                if started_transaction:
                    conn.commit()
                return None
            command = dict(row)
            cursor.execute(
                """
                UPDATE scraper_runtime_commands
                SET status = 'processing', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                """,
                (command["id"],),
            )
            if cursor.rowcount == 0:
                if started_transaction:
                    conn.commit()
                return None
            if started_transaction:
                conn.commit()
            command["payload"] = self._decode_payload(command.get("payload"))
            command["status"] = "processing"
            return command
        except Exception:
            if started_transaction or managed_conn:
                conn.rollback()
            raise
        finally:
            cursor.close()
            if managed_conn:
                conn.close()

    def complete_command(self, command_id: int, result_message: Optional[str] = None) -> None:
        self._set_command_status(command_id, "completed", result_message)

    def fail_command(self, command_id: int, result_message: Optional[str] = None) -> None:
        self._set_command_status(command_id, "failed", result_message)

    def cancel_pending_run_commands(self, scraper_name: str) -> int:
        cursor = self.execute(
            """
            UPDATE scraper_runtime_commands
            SET status = 'cancelled', result_message = 'Cancelled before execution', updated_at = CURRENT_TIMESTAMP
            WHERE scraper_name = ? AND command_type = 'run' AND status = 'pending'
            """,
            (scraper_name,),
        )
        return cursor.rowcount

    def delete_commands_for_scraper(self, scraper_name: str) -> None:
        self.execute("DELETE FROM scraper_runtime_commands WHERE scraper_name = ?", (scraper_name,))

    def _set_command_status(self, command_id: int, status: str, result_message: Optional[str]) -> None:
        self.execute(
            """
            UPDATE scraper_runtime_commands
            SET status = ?, result_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, result_message, command_id),
        )

    @staticmethod
    def _decode_payload(payload: Optional[str]) -> Dict:
        if not payload:
            return {}
        try:
            return json.loads(payload)
        except Exception:
            return {}
