import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 查询 type 字段分布
c.execute('SELECT type, COUNT(*) as count FROM news GROUP BY type')
results = c.fetchall()

print('news 表中 type 字段分布:')
for r in results:
    type_val = r[0] if r[0] else 'NULL/Empty'
    count = r[1]
    print(f'  type="{type_val}": {count} 条')

# 查询未设置 type 的记录
c.execute('SELECT COUNT(*) FROM news WHERE type IS NULL OR type = ""')
null_count = c.fetchone()[0]
print(f'\n未设置 type 的记录: {null_count} 条')

# 查询总记录数
c.execute('SELECT COUNT(*) FROM news')
total = c.fetchone()[0]
print(f'总记录数: {total} 条')

# 查看几个示例
print('\n示例记录（前5条）:')
c.execute('SELECT id, title, type, source_site FROM news LIMIT 5')
samples = c.fetchall()
for s in samples:
    print(f'  ID={s[0]}: type="{s[2] if s[2] else \"NULL\"}", source={s[3]}, title={s[1][:30]}...')

conn.close()
