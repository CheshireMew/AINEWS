from typing import Dict, List, Optional, Union
import sqlite3

from shared.db_base import DatabaseBase


class QueryResult:
    def __init__(self, rows: Optional[List] = None, rowcount: int = 0, lastrowid: Optional[int] = None):
        self._rows = rows or []
        self._position = 0
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def fetchone(self):
        if self._position >= len(self._rows):
            return None
        row = self._rows[self._position]
        self._position += 1
        return row

    def fetchall(self):
        rows = self._rows[self._position:]
        self._position = len(self._rows)
        return rows


class BaseRepository:
    def __init__(self, db_or_conn: Union[DatabaseBase, sqlite3.Connection]):
        self.conn = None
        self.db = None

        if isinstance(db_or_conn, sqlite3.Connection):
            self.conn = db_or_conn
        else:
            self.db = db_or_conn

    def execute(self, query: str, params: tuple = ()) -> QueryResult:
        managed_conn = self.conn is None
        conn = self.conn or self.db.connect()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall() if cursor.description else []
            if managed_conn and query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
                conn.commit()
            return QueryResult(rows=rows, rowcount=cursor.rowcount, lastrowid=cursor.lastrowid)
        except Exception as exc:
            conn.rollback()
            raise exc
        finally:
            cursor.close()
            if managed_conn:
                conn.close()

    def paginated_query(self, table: str, page: int = 1, limit: int = 50, fields: str = '*', where: str = '1=1', where_params: tuple = (), order_by: str = 'id DESC') -> Dict:
        offset = (page - 1) * limit
        count_cursor = self.execute(f'SELECT COUNT(*) as total FROM {table} WHERE {where}', where_params)
        total_row = count_cursor.fetchone()
        total = total_row['total'] if isinstance(total_row, sqlite3.Row) else total_row[0]

        data_cursor = self.execute(
            f'SELECT {fields} FROM {table} WHERE {where} ORDER BY {order_by} LIMIT ? OFFSET ?',
            where_params + (limit, offset),
        )
        rows = data_cursor.fetchall()
        results = [dict(row) for row in rows]

        return {
            'results': results,
            'total': total,
            'page': page,
            'limit': limit,
        }
