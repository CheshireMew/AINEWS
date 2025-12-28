import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("检查ID 1223和1241")
print("="*60)

rows = cursor.execute('''
    SELECT id, title, published_at, duplicate_of 
    FROM news 
    WHERE id IN (1223, 1241)
    ORDER BY published_at
''').fetchall()

if len(rows) < 2:
    print("找不到这两条新闻")
else:
    for row in rows:
        print(f"\nID {row[0]}:")
        print(f"  时间: {row[2]}")
        print(f"  duplicate_of: {row[3]}")
        print(f"  标题: {row[1]}")
        
        # 检查有多少duplicate指向它
        dup_count = cursor.execute(
            'SELECT COUNT(*) FROM news WHERE duplicate_of = ?', (row[0],)
        ).fetchone()[0]
        print(f"  作为master: {dup_count}条duplicate指向它")

print("\n" + "="*60)
print("分析")
print("="*60)
print("相似度65.88% > 阈值50%，应该被判重")
print("\n可能原因：")
print("1. 去重时使用了时间窗口限制（默认24小时）")
print("2. 两条新闻都已经是master，master合并逻辑未生效")
print("3. 需要重新运行去重")

conn.close()
