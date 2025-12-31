import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("=== system_config 表中的爬虫配置 ===\n")

# 查找爬虫相关的配置
c.execute("SELECT key, value, updated_at FROM system_config WHERE key LIKE 'scraper_config%' ORDER BY key")
rows = c.fetchall()

if rows:
    for row in rows:
        print(f"Key: {row[0]}")
        print(f"Value: {row[1]}")
        print(f"Updated: {row[2]}")
        print("-" * 50)
else:
    print("未找到爬虫配置")

# 查看所有配置
print("\n=== 所有配置项 ===\n")
c.execute("SELECT key FROM system_config ORDER BY key")
all_keys = c.fetchall()
for key in all_keys:
    print(f"  - {key[0]}")

conn.close()
