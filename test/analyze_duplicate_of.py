import sys
sys.path.insert(0, '.')
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("="*100)
print("详细检查当前数据库duplicate_of值的分布")
print("="*100)

# 统计所有非NULL的duplicate_of值
c.execute("""
    SELECT duplicate_of, COUNT(*) as count
    FROM news
    WHERE duplicate_of IS NOT NULL
    GROUP BY duplicate_of
    ORDER BY count DESC
    LIMIT 20
""")

print("\nduplicate_of值的分布（前20个）:")
print(f"{'duplicate_of值':<15} {'数量':<10} {'可能含义'}")
print("-"*100)

for row in c.fetchall():
    dup_of = row[0]
    count = row[1]
    
    # 判断这个值是ID还是索引
    if dup_of < 10:
        meaning = "⚠️ 可能是列表索引（太小了）"
    elif dup_of == 10:
        meaning = "❌ 黄金新闻ID（大量误判的目标）"
    else:
        meaning = "✅ 可能是正常的新闻ID"
    
    print(f"{dup_of:<15} {count:<10} {meaning}")

# 特别检查duplicate_of=10的情况
print("\n" + "="*100)
print("检查duplicate_of=10的具体记录（最近5条）")
print("="*100)

c.execute("""
    SELECT id, title, duplicate_of, updated_at
    FROM news
    WHERE duplicate_of = 10
    ORDER BY updated_at DESC
    LIMIT 5
""")

for row in c.fetchall():
    print(f"\nID {row[0]}: {row[1][:70]}")
    print(f"  duplicate_of: {row[2]}")
    print(f"  更新时间: {row[3]}")

conn.close()

print("\n" + "="*100)
print("分析结论")
print("="*100)
print("如果duplicate_of都是像10这样的正常ID → 说明修复生效了，但业务逻辑有问题")
print("如果duplicate_of有0,1,2这样的小值 → 说明修复未生效，仍在使用索引")
print("="*100)
