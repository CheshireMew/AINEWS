import sys
sys.path.insert(0, '.')

import sqlite3
from datetime import datetime

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("完整数据流诊断")
print("="*80)

# 1. 检查黄金新闻
print("\n1. 黄金新闻基本信息:")
cursor.execute("SELECT id, title, published_at, stage FROM news WHERE id = 10")
gold = cursor.fetchone()
print(f"   ID: {gold[0]}")
print(f"   标题: {gold[1]}")
print(f"   发布时间: {gold[2]}")
print(f"   阶段: {gold[3]}")

# 2. 统计所有标记为重复黄金新闻的数量
print(f"\n2. 被标记为重复黄金新闻(ID=10)的新闻数量:")
cursor.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = 10")
count = cursor.fetchone()[0]
print(f"   总计: {count} 条")

# 3. 列出所有被误标记的新闻
print(f"\n3. 被误标记的新闻列表（前10条）:")
cursor.execute("""
    SELECT id, title, published_at, stage, updated_at
    FROM news 
    WHERE duplicate_of = 10
    ORDER BY id
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"\n   ID {row[0]}: {row[1][:70]}")
    print(f"     发布时间: {row[2]}")
    print(f"     更新时间: {row[4]}")
    print(f"     阶段: {row[3]}")
    
    # 计算与黄金新闻的时间差
    try:
        gold_time = datetime.fromisoformat(gold[2].replace('Z', '+00:00'))
        news_time = datetime.fromisoformat(row[2].replace('Z', '+00:00'))
        diff_hours = abs((gold_time - news_time).total_seconds() / 3600)
        print(f"     时间差: {diff_hours:.1f} 小时")
    except:
        print(f"     时间差: 无法计算")

# 4. 检查news表的ID范围和时间范围
print(f"\n4. 数据库整体信息:")
cursor.execute("SELECT MIN(id), MAX(id), COUNT(*) FROM news")
min_id, max_id, total = cursor.fetchone()
print(f"   ID范围: {min_id} - {max_id}")
print(f"   总新闻数: {total}")

cursor.execute("SELECT MIN(published_at), MAX(published_at) FROM news")
min_time, max_time = cursor.fetchone()
print(f"   时间范围: {min_time} 到 {max_time}")

conn.close()

print("\n" + "="*80)
print("诊断完成")
print("="*80)
