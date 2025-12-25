import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 查找包含"日本央行"的最新新闻
c.execute("""
    SELECT id, title, content, scraped_at 
    FROM news 
    WHERE source_site='blockbeats' AND title LIKE '%日本央行%'
    ORDER BY id DESC 
    LIMIT 1
""")

row = c.fetchone()
if row:
    row_id, title, content, scraped_at = row
    print(f"ID: {row_id}")
    print(f"Title: {title[:60]}")
    print(f"Scraped: {scraped_at}")
    print(f"\n内容中的连续换行统计:")
    print(f"  单换行 (\\n): {content.count(chr(10))}")
    print(f"  双换行 (\\n\\n): {content.count(chr(10)*2)}")
    print(f"  三换行 (\\n\\n\\n): {content.count(chr(10)*3)}")
    print(f"  四换行 (\\n\\n\\n\\n): {content.count(chr(10)*4)}")
    
    print(f"\n内容 (repr, 前500字符):")
    print(repr(content[:500]))
else:
    print("未找到相关新闻")

conn.close()
