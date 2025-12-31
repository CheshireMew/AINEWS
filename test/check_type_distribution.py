"""
验证各个数据表中的 type 分布
检查是否有文章混入快讯数据
"""
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("="*70)
print("数据类型分布检查".center(70))
print("="*70)

# 1. news 表
print("\n1. news 表 (原始数据):")
c.execute("SELECT type, COUNT(*) FROM news GROUP BY type")
for row in c.fetchall():
    print(f"   {row[0]}: {row[1]} 条")

# 2. deduplicated_news 表
print("\n2. deduplicated_news 表 (去重数据):")
c.execute("SELECT type, COUNT(*) FROM deduplicated_news GROUP BY type")
for row in c.fetchall():
    print(f"   {row[0]}: {row[1]} 条")

# 3. curated_news 表  
print("\n3. curated_news 表 (精选数据):")
c.execute("SELECT type, COUNT(*) FROM curated_news GROUP BY type")
for row in c.fetchall():
    print(f"   {row[0]}: {row[1]} 条")

# 4. curated_news 按 ai_status 分组
print("\n4. curated_news 按 AI 状态分组:")
c.execute("SELECT type, ai_status, COUNT(*) FROM curated_news GROUP BY type, ai_status")
for row in c.fetchall():
    print(f"   type={row[0]}, ai_status={row[1]}: {row[2]} 条")

# 5. 检查最近的文章
print("\n5. 最近的文章 (top 5):")
c.execute("SELECT id, title, type, source_site FROM news WHERE type='article' ORDER BY published_at DESC LIMIT 5")
for row in c.fetchall():
    print(f"   ID={row[0]}, type={row[2]}, source={row[3]}")
    print(f"      标题: {row[1][:50]}...")

conn.close()

print("\n" + "="*70)
print("检查完成".center(70))
print("="*70)
