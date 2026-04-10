"""数据库操作基类。"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple


class DatabaseBase:
    """数据库操作基类，提供通用的 CRUD 和查询方法。"""

    @contextmanager
    def get_cursor(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict]:
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid

    def paginated_query(
        self,
        table: str,
        fields: str = "*",
        where: str = "1=1",
        where_params: Tuple = (),
        order_by: str = "id DESC",
        page: int = 1,
        limit: int = 50,
    ) -> Dict[str, Any]:
        offset = (page - 1) * limit
        query = f"SELECT {fields} FROM {table} WHERE {where} ORDER BY {order_by} LIMIT ? OFFSET ?"
        data = self.execute_query(query, where_params + (limit, offset))

        count_query = f"SELECT COUNT(*) as total FROM {table} WHERE {where}"
        total_row = self.execute_one(count_query, where_params)
        total = total_row["total"] if total_row else 0

        return {
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
        }
