import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 检查各个stage的新闻数量
cursor.execute('SELECT stage, COUNT(*) FROM news GROUP BY stage')
stages = cursor.fetchall()

print('\n新闻状态统计:')
print('=' * 50)
for stage, count in stages:
    print(f'{stage}: {count}')

# 检查 deduplicated_news 表
cursor.execute('SELECT COUNT(*) FROM deduplicated_news')
dedup_count = cursor.fetchone()[0]
print(f'\ndeduplicated_news 表: {dedup_count}')

# 检查是否有 duplicate_of 不为空但 stage 不是 duplicate 的
cursor.execute('''
    SELECT COUNT(*) 
    FROM news 
    WHERE duplicate_of IS NOT NULL AND stage != 'duplicate'
''')
inconsistent = cursor.fetchone()[0]
print(f'\n不一致的数据(有duplicate_of但stage不是duplicate): {inconsistent}')

conn.close()
