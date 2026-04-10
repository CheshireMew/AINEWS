from typing import List, Optional

from .base_repository import BaseRepository


class ApiKeyRepository(BaseRepository):
    def get_analyst_api_keys(self):
        try:
            cursor = self.execute('SELECT id, key_name, api_key, notes, enabled, created_at, last_used_at FROM api_keys ORDER BY id DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取 API Key 失败: {e}")
            return []

    def create_analyst_api_key(self, key_name: str, api_key: str, notes: Optional[str]):
        try:
            cursor = self.execute(
                'INSERT INTO api_keys (key_name, api_key, notes, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
                (key_name, api_key, notes),
            )
            return cursor.lastrowid
        except Exception as e:
            print(f"创建 API Key 失败: {e}")
            return None

    def delete_analyst_api_key(self, key_id: int) -> bool:
        try:
            cursor = self.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
            return cursor.rowcount > 0
        except Exception as e:
            print(f"删除 API Key 失败: {e}")
            return False
