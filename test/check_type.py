import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

try:
    # 查询 type 字段分布
    c.execute('SELECT COALESCE(type, "NULL") as type_val, COUNT(*) as count FROM news GROUP BY type')
    results = c.fetchall()
    
    print('=== news 表中 type 字段分布 ===')
    for r in results:
        print(f'  type="{r[0]}": {r[1]} 条')
    
    # 查询总记录数
    c.execute('SELECT COUNT(*) FROM news')
    total = c.fetchone()[0]
    print(f'\n总记录数: {total} 条')
    
    # 查看示例
    print('\n=== 示例记录（前5条）===')
    c.execute('SELECT id, title, type, source_site FROM news ORDER BY id DESC LIMIT 5')
    samples = c.fetchall()
    for s in samples:
        type_val = s[2] if s[2] else 'NULL'
        title = s[1][:40] if s[1] else 'N/A'
        print(f'  ID={s[0]}: type="{type_val}", source={s[3]}, title={title}...')
    
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
