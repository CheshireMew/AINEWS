import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("调查ID 1070和1078的异常标记")
print("="*80)

# 获取这两条新闻
rows = cursor.execute('''
    SELECT id, title, duplicate_of, duplicate_reason
    FROM news 
    WHERE id IN (1070, 1078)
    ORDER BY id
''').fetchall()

print("\n【新闻详情】")
for row in rows:
    print(f"\nID {row[0]}:")
    print(f"  标题: {row[1]}")
    print(f"  duplicate_of: {row[2]}")
    print(f"  原因: {row[3]}")

# 查看1070的所有duplicates
print("\n" + "="*80)
print("ID 1070的所有duplicates")
print("="*80)

dups = cursor.execute('''
    SELECT id, title, duplicate_reason
    FROM news 
    WHERE duplicate_of = 1070
    ORDER BY id
''').fetchall()

print(f"\n共 {len(dups)} 条duplicate:")
for dup in dups:
    print(f"\nID {dup[0]}: {dup[1][:60]}")
    print(f"  原因: {dup[2]}")

# 检查1078是否原本指向其他新闻，后来被合并到1070
print("\n" + "="*80)
print("分析")
print("="*80)

# 看duplicate_reason中是否提到"master合并"
merge_count = sum(1 for d in dups if d[2] and 'master合并' in d[2])
print(f"\n通过master合并来的: {merge_count}条")
print(f"直接相似判定的: {len(dups) - merge_count}条")

if any(d[0] == 1078 for d in dups):
    target_dup = next(d for d in dups if d[0] == 1078)
    print(f"\nID 1078的标记原因: {target_dup[2]}")
    
    if 'master合并' in (target_dup[2] or ''):
        print("\n⚠️ 这是master合并导致的！")
        print("可能流程:")
        print("1. 1078原本指向某个新闻X")
        print("2. 后来发现X和1070相似")
        print("3. Master合并：将所有指向X的改为指向1070")
        print("4. 但X和1070可能不够相似！")
    else:
        print("\n❌ 这是直接相似判定！")
        print("算法bug：15.34%的相似度不应该被判重！")

conn.close()
