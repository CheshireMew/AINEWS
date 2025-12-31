import sqlite3

conn = sqlite3.connect('data/news.db')
cursor = conn.cursor()

cursor.execute('SELECT name, url, type, enabled FROM sources ORDER BY id')
sources = cursor.fetchall()

print(f'已配置的爬虫数量: {len(sources)}\n')
print('='*80)
print('爬虫列表:')
print('='*80)

for i, source in enumerate(sources, 1):
    name, url, stype, enabled = source
    print(f"\n{i}. {name}")
    print(f"   URL: {url}")
    print(f"   类型: {stype}")
    print(f"   启用: {'是' if enabled else '否'}")

conn.close()
