"""数据库配置 - 自动选择SQLite或PostgreSQL"""
import os

# 检查是否配置了PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL', '')

if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    # 使用PostgreSQL
    print("🐘 使用PostgreSQL数据库")
    from database.db import Database
else:
    # 使用SQLite
    print("🪶 使用SQLite数据库")
    from .db_sqlite import Database

__all__ = ['Database']
