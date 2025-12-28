import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 查找剩余的master
masters = cursor.execute('''
    SELECT id, title 
    FROM news 
    WHERE duplicate_of IS NULL 
      AND id IN (SELECT DISTINCT duplicate_of FROM news WHERE duplicate_of IS NOT NULL)
''').fetchall()

print("剩余的1个有重复的master:")
print("="*80)

for m in masters:
    print(f"\nID {m[0]}: {m[1]}")
    
    # 查看duplicates
    dups = cursor.execute('''
        SELECT id, title 
        FROM news 
        WHERE duplicate_of = ?
    ''', (m[0],)).fetchall()
    
    print(f"  有 {len(dups)} 条duplicate:")
    for d in dups:
        print(f"    ID {d[0]}: {d[1][:70]}")

conn.close()

print("\n" + "="*80)
print("这是正常的，现在可以重新运行去重")
