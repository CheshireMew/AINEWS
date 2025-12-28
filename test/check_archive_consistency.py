import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 检查是否有重复的 original_news_id
cursor.execute('''
    SELECT original_news_id, COUNT(*) as cnt
    FROM deduplicated_news
    WHERE original_news_id IS NOT NULL
    GROUP BY original_news_id
    HAVING cnt > 1
''')

duplicates = cursor.fetchall()
print(f'\ndeduplicated_news 表中重复的 original_news_id: {len(duplicates)}')
if duplicates:
    for oid, cnt in duplicates[:5]:
        print(f'  original_news_id={oid}: {cnt} 次')

# 检查 news 表中 stage=deduplicated 但在 deduplicated_news 表中不存在的
cursor.execute('''
    SELECT n.id, n.title
    FROM news n
    LEFT JOIN deduplicated_news d ON n.id = d.original_news_id
    WHERE n.stage = 'deduplicated' AND d.id IS NULL
    LIMIT 10
''')

missing = cursor.fetchall()
print(f'\nstage=deduplicated 但未在 deduplicated_news 表中的: {len(missing)}')
if missing:
    for nid, title in missing:
        print(f'  ID {nid}: {title[:50]}...')

conn.close()
