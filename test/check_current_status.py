import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 检查当前所有新闻的状态分布
cursor.execute('''
    SELECT stage, COUNT(*) 
    FROM news 
    GROUP BY stage
''')

print('\n当前 news 表状态分布:')
print('=' * 50)
for stage, count in cursor.fetchall():
    print(f'{stage}: {count}')

# 检查 deduplicated_news 表
cursor.execute('SELECT COUNT(*) FROM deduplicated_news')
dedup_count = cursor.fetchone()[0]
print(f'\ndeduplicated_news 表: {dedup_count} 条')

# 检查有多少重复关系
cursor.execute('SELECT COUNT(*) FROM news WHERE duplicate_of IS NOT NULL')
has_dup_of = cursor.fetchone()[0]
print(f'\n有 duplicate_of 字段的: {has_dup_of} 条')

conn.close()
