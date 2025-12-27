import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("=== BlockBeats 最新3条 ===")
cursor.execute('''
    SELECT id, title, published_at, scraped_at 
    FROM news 
    WHERE source_site='blockbeats' 
    ORDER BY id DESC 
    LIMIT 3
''')

for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"标题: {row[1][:40]}")
    print(f"发布时间: {row[2]}")
    print(f"抓取时间: {row[3]}")
    print(f"相等? {row[2] == row[3]}")
    print()

print("\n=== ChainCatcher 最新3条 ===")
cursor.execute('''
    SELECT id, title, published_at, scraped_at 
    FROM news 
    WHERE source_site='chaincatcher' 
    ORDER BY id DESC 
    LIMIT 3
''')

for row in cursor.fetchall():
    print(f"ID: {row[0]}")
    print(f"标题: {row[1][:40]}")
    print(f"发布时间: {row[2]}")
    print(f"抓取时间: {row[3]}")
    print(f"相等? {row[2] == row[3]}")
    print()

conn.close()
