import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("检查 AI 精选中的文章记录")
print("=" * 70)

# 检查 ID 6661 和 6662
ids = [6661, 6662]

for table in ['news', 'deduplicated_news', 'curated_news']:
    print(f"\n{table} 表:")
    for id in ids:
        c.execute(f"SELECT id, title, type, source_site FROM {table} WHERE id = ?", (id,))
        row = c.fetchone()
        if row:
            print(f"  ID {row[0]}: type='{row[2]}', source='{row[3]}'")
            print(f"    标题: {row[1][:40]}...")
        else:
            print(f"  ID {id}: 未找到")

# 检查 curated_news 中所有文章类型的记录
print("\n" + "=" * 70)
print("curated_news 表中的文章记录 (type='article'):")
c.execute("SELECT id, title, type, ai_status FROM curated_news WHERE type = 'article' LIMIT 10")
rows = c.fetchall()
for row in rows:
    print(f"  ID {row[0]}: type={row[2]}, ai_status={row[3]}")
    print(f"    {row[1][:60]}...")

conn.close()
