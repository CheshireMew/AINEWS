"""
修复数据不一致问题：
将 stage='duplicate' 但 duplicate_of=NULL 的新闻改为 stage='raw'
"""
import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 查找问题数据
cursor.execute("""
    SELECT id, title 
    FROM news 
    WHERE stage = 'duplicate' AND duplicate_of IS NULL
""")

rows = cursor.fetchall()
print(f'\n发现 {len(rows)} 条状态不一致的新闻')
print('=' * 80)

if rows:
    print('\n这些新闻将被重置为 stage="raw"，以便重新去重:\n')
    for r in rows:
        title = r[1][:60] + '...' if len(r[1]) > 60 else r[1]
        print(f'  ID {r[0]}: {title}')
    
    # 修复
    cursor.execute("""
        UPDATE news 
        SET stage = 'raw' 
        WHERE stage = 'duplicate' AND duplicate_of IS NULL
    """)
    
    conn.commit()
    print(f'\n✅ 已将 {cursor.rowcount} 条新闻重置为 raw 状态')
    print('现在可以重新运行去重，这些新闻会被正确处理。')
else:
    print('✅ 没有发现状态不一致的数据')

conn.close()
