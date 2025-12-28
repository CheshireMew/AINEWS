import sys
sys.path.insert(0, '.')

import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 检查问题新闻更新时间
curse = conn.cursor()
cursor.execute("""
    SELECT id, title, duplicate_of, updated_at, published_at
    FROM news 
    WHERE id IN (10, 1160, 1161, 1159, 1154)
    ORDER BY id
""")

print("新闻状态检查:")
for row in cursor.fetchall():
    print(f"ID {row[0]}:")
    print(f"  标题: {row[1][:60]}")
    print(f"  duplicate_of: {row[2]}")
    print(f"  updated_at: {row[3]}")
    print(f"  published_at: {row[4]}")
    print()

conn.close()
