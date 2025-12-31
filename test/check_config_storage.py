import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 查找配置相关的表
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%config%'")
tables = c.fetchall()

print("配置相关的表:")
for table in tables:
    print(f"  - {table[0]}")

# 如果有 system_config 表，查看其内容
if any('system_config' in t[0] for t in tables):
    print("\nsystem_config 表内容:")
    c.execute("SELECT * FROM system_config LIMIT 10")
    rows = c.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()
