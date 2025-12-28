import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("深入诊断：为什么ID 24和65没有被判定为重复")
print("="*80)

# 获取详细信息
rows = cursor.execute('''
    SELECT id, title, published_at, duplicate_of
    FROM news 
    WHERE id IN (24, 65)
    ORDER BY published_at
''').fetchall()

print("\n按时间排序:")
for row in rows:
    print(f"ID {row[0]}: {row[2]} - duplicate_of={row[3]}")
    print(f"  {row[1][:70]}")

# 检查谁指向它们
print("\n各自的duplicates:")
for news_id in [24, 65]:
    dups = cursor.execute(f'SELECT id, title FROM news WHERE duplicate_of = {news_id}').fetchall()
    if dups:
        print(f"\n指向ID {news_id}的:")
        for d in dups:
            print(f"  ID {d[0]}: {d[1][:60]}")
    else:
        print(f"\n指向ID {news_id}的: 无")

# 检查是否有交叉引用
print("\n" + "="*80)
print("可能的原因分析")
print("="*80)

# ID较小的应该是master
if rows[0][0] == 24:
    earlier_id = 24
    later_id = 65
    earlier_time = rows[0][2]
    later_time = rows[1][2]
else:
    earlier_id = 65
   later_id = 24
    earlier_time = rows[1][2]
    later_time = rows[0][2]

print(f"\n按ID和时间判断:")
print(f"  更早: ID {earlier_id} at {earlier_time}")
print(f"  更晚: ID {later_id} at {later_time}")

# 检查是否都已经作为master
cursor.execute('''
    SELECT 
        (SELECT COUNT(*) FROM news WHERE duplicate_of = 24) as count_24,
        (SELECT COUNT(*) FROM news WHERE duplicate_of = 65) as count_65
''')
counts = cursor.fetchone()

print(f"\n作为master的状态:")
print(f"  ID 24: {counts[0]}条duplicate指向它")
print(f"  ID 65: {counts[1]}条duplicate指向它")

if counts[0] > 0 and counts[1] > 0:
    print("\n✓ 发现根本原因：")
    print("  两者都已经是master（各有duplicate指向它们）")
    print("  三重检查中的'duplicate不能曾作为master'规则阻止了标记")
    print(f"  即：不能让ID {later_id}指向ID {earlier_id}，因为{later_id}已经是master")

conn.close()
