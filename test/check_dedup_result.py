import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 检查去重前的状态
cursor.execute("""
    SELECT stage, COUNT(*) 
    FROM news 
    WHERE stage IN ('raw', 'deduplicated')
    GROUP BY stage
""")

print('\n去重前的新闻状态:')
for stage, count in cursor.fetchall():
    print(f'  {stage}: {count}')

# 检查去重结果
cursor.execute("SELECT COUNT(*) FROM news WHERE duplicate_of IS NOT NULL")
has_duplicate_of = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM news WHERE stage = 'duplicate'")
duplicate_stage = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM news WHERE is_local_duplicate = 1")
is_local_duplicate = cursor.fetchone()[0]

print(f'\n去重结果:')
print(f'  有 duplicate_of 字段的: {has_duplicate_of}')
print(f'  stage=duplicate 的: {duplicate_stage}')
print(f'  is_local_duplicate=1 的: {is_local_duplicate}')

conn.close()
