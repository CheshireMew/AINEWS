from __future__ import annotations

from contextlib import contextmanager

from .sqlite.db_sqlite import Database


database = Database()


def init_database() -> None:
    database.init_db()


@contextmanager
def db_connection():
    conn = database.connect()
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def transaction():
    with db_connection() as conn:
        try:
            conn.execute("BEGIN")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
