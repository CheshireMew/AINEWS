import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()
c.execute('SELECT id, title, content FROM news WHERE source_site=? ORDER BY id DESC LIMIT 2', ('blockbeats',))
rows = c.fetchall()

for row_id, title, content in rows:
    print(f"\n{'='*80}")
    print(f"ID: {row_id}")
    print(f"Title: {title[:60]}")
    print(f"\n=== Content (repr) ===")
    print(repr(content[:500]))
    print(f"\n=== Content (display) ===")
    print(content[:500])
    print(f"{'='*80}\n")

conn.close()
