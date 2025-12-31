import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 模拟 load_last_news 的查询
site_name = 'ForesightNews 独家'

print(f"Querying for site_name = '{site_name}'")
print("="*60)

c.execute('''
    SELECT source_url, title, published_at, scraped_at 
    FROM news 
    WHERE source_site = ? 
    ORDER BY published_at DESC 
    LIMIT 10
''', (site_name,))

rows = c.fetchall()
print(f"\nFound {len(rows)} records (showing top 10 by published_at DESC):\n")

for i, row in enumerate(rows, 1):
    print(f"{i}. URL: .../{row[0].split('/')[-1]}")
    print(f"   Title: {row[1][:40]}...")
    print(f"   Published: {row[2]}")
    print(f"   Scraped: {row[3]}")
    print()

# 检查 93570 是否在其中
urls = [r[0] for r in rows]
target = 'https://foresightnews.pro/article/detail/93570'
if target in urls:
    print(f"✓ Target URL {target} IS in the result set")
else:
    print(f"✗ Target URL {target} NOT in top 10 results")
    # 检查它rank多少
    c.execute('''
        SELECT COUNT(*) FROM news 
        WHERE source_site = ? AND published_at > (
            SELECT published_at FROM news WHERE source_url = ?
        )
    ''', (site_name, target))
    rank = c.fetchone()[0] + 1
    print(f"  It ranks #{rank} in published_at DESC order")

conn.close()
