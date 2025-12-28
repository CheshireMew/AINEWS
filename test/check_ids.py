import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("检查ID 24和65的详细信息")
print("="*80)

# 获取两条新闻
rows = cursor.execute('''
    SELECT id, title, published_at, duplicate_of 
    FROM news 
    WHERE id IN (24, 65)
    ORDER BY id
''').fetchall()

print("\n新闻1 (ID 24):")
print(f"  标题: {rows[0][1]}")
print(f"  时间: {rows[0][2]}")
print(f"  duplicate_of: {rows[0][3]}")

print("\n新闻2 (ID 65):")
print(f"  标题: {rows[1][1]}")
print(f"  时间: {rows[1][2]}")
print(f"  duplicate_of: {rows[1][3]}")

# 检查谁指向它们
dup24 = cursor.execute('SELECT id, title FROM news WHERE duplicate_of = 24').fetchall()
dup65 = cursor.execute('SELECT id, title FROM news WHERE duplicate_of = 65').fetchall()

if dup24:
    print(f"\n指向24的新闻:")
    for d in dup24:
        print(f"  ID {d[0]}: {d[1][:60]}")

if dup65:
    print(f"\n指向65的新闻:")
    for d in dup65:
        print(f"  ID {d[0]}: {d[1][:60]}")

conn.close()

print("\n" + "="*80)
print("结论")
print("="*80)
print("这两条新闻本身都是master（duplicate_of = NULL）")
print("各自有1条duplicate指向它们")
print("但24和65本身没有被判定为相似")
print("\n可能原因：")
print("1. 相似度计算结果低于阈值0.50")
print("2. 不是链式限制的问题（它们都是独立的master）")
print("3. 需要优化相似度算法或降低阈值")
