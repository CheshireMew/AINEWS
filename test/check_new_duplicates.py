import sys
sys.path.insert(0, '.')
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("="*80)
print("检查新误判记录")
print("="*80)

# 检查用户提到的新ID
new_ids = [1166, 1167, 1164, 1162]

for news_id in new_ids:
    c.execute("""
        SELECT id, title, duplicate_of, stage, updated_at, published_at
        FROM news
        WHERE id = ?
    """, (news_id,))
    
    row = c.fetchone()
    if row:
        print(f"\nID {row[0]}:")
        print(f"  标题: {row[1][:70]}")
        print(f"  duplicate_of: {row[2]}")
        print(f"  stage: {row[3]}")
        print(f"  更新时间: {row[4]}")
        print(f"  发布时间: {row[5]}")

# 检查是否还有其他duplicate_of=10的记录
print("\n" + "="*80)
print("检查当前所有duplicate_of=10的记录数量")
print("="*80)
c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = 10")
count = c.fetchone()[0]
print(f"总数: {count}")

if count > 0:
    c.execute("""
        SELECT id, title, updated_at 
        FROM news 
        WHERE duplicate_of = 10 
        ORDER BY updated_at DESC 
        LIMIT 10
    """)
    print("\n最近更新的前10条:")
    for row in c.fetchall():
        print(f"  ID {row[0]}: {row[1][:50]}... (更新于: {row[2]})")

conn.close()
