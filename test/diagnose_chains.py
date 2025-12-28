import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 查询这几条可疑新闻
rows = cursor.execute('''
    SELECT id, SUBSTR(title, 1, 60) as title, duplicate_of 
    FROM news 
    WHERE id IN (1230, 1220, 1236)
    ORDER BY id
''').fetchall()

print("="*80)
print("可疑新闻的duplicate_of关系:")
print("="*80)
for id, title, dup_of in rows:
    print(f"ID {id}: duplicate_of={dup_of}")
    print(f"  标题: {title}")
    print()

# 查找所有链式结构
print("="*80)
print("查找链式结构（duplicate指向另一个duplicate）:")
print("="*80)

chain_query = '''
    SELECT n1.id, n1.duplicate_of, n2.duplicate_of as master_duplicate_of
    FROM news n1
    JOIN news n2 ON n1.duplicate_of = n2.id
    WHERE n1.duplicate_of IS NOT NULL 
      AND n2.duplicate_of IS NOT NULL
    LIMIT 10
'''

chains = cursor.execute(chain_query).fetchall()
if chains:
    print(f"发现 {len(chains)} 个链式结构:")
    for child_id, parent_id, grandparent_id in chains:
        print(f"  {child_id} -> {parent_id} -> {grandparent_id}")
else:
    print("✅ 没有发现链式结构")

conn.close()
