import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("=== author 字段测试 ===\n")

# 1. 检查 schema
c.execute("PRAGMA table_info(news)")
columns = c.fetchall()
column_names = [col[1] for col in columns]

if 'author' in column_names:
    print("✅ news 表已包含 author 字段")
else:
    print("❌ news 表缺少 author 字段")
    conn.close()
    exit(1)

# 2. 查看现有数据的 author 值分布
c.execute("SELECT author, COUNT(*) FROM news GROUP BY author LIMIT 10")
results = c.fetchall()
print("\nauthor 字段值分布:")
for r in results:
    author = r[0] if r[0] else 'NULL/Empty'
    count = r[1]
    print(f"  {author}: {count} 条")

# 3. 查看最新的几条记录
print("\n最新 5 条记录:")
c.execute("SELECT id, title, author, type FROM news ORDER BY id DESC LIMIT 5")
samples = c.fetchall()
for s in samples:
    print(f"  ID={s[0]}: author='{s[2] if s[2] else 'NULL'}', type='{s[3]}', title={s[1][:40]}...")

conn.close()
print("\n✅ 测试完成")
