import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 查找状态不一致的新闻
cursor.execute("""
    SELECT id, title, duplicate_of, stage 
    FROM news 
    WHERE stage = 'duplicate' AND duplicate_of IS NULL 
    LIMIT 20
""")

rows = cursor.fetchall()
print(f'\n发现 {len(rows)} 条状态不一致的新闻:')
print('=' * 80)

for r in rows:
    print(f'ID {r[0]}: stage={r[3]}, duplicate_of={r[2]}')
    print(f'  标题: {r[1][:50]}...' if len(r[1]) > 50 else f'  标题: {r[1]}')
    print()

conn.close()
