"""追踪数据流：检查API端点如何处理去重结果"""
import sys
sys.path.insert(0, '.')
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("="*100)
print("检查数据库中的实际duplicate_of值")
print("="*100)

# 查看最近的duplicate_of记录
print("\n最近被标记为重复的记录（按更新时间）:")
c.execute("""
    SELECT id, title, duplicate_of, updated_at, stage
    FROM news
    WHERE duplicate_of IS NOT NULL
    ORDER BY updated_at DESC
    LIMIT 20
""")

for row in c.fetchall():
    print(f"\nID {row[0]}: duplicate_of={row[2]}")
    print(f"  标题: {row[1][:70]}")
    print(f"  更新时间: {row[3]}")
    print(f"  stage: {row[4]}")

# 统计duplicate_of的分布
print("\n" + "="*100)
print("duplicate_of值的分布:")
print("="*100)

c.execute("""
    SELECT duplicate_of, COUNT(*) as cnt
    FROM news
    WHERE duplicate_of IS NOT NULL
    GROUP BY duplicate_of
    ORDER BY cnt DESC
    LIMIT 10
""")

print("\nduplicate_of | 记录数 | 是否异常")
print("-" * 60)
for row in c.fetchall():
    dup_of = row[0]
    count = row[1]
    is_blackhole = "🔴 黑洞!" if count > 10 else "✅"
    print(f"{dup_of:12} | {count:6} | {is_blackhole}")

conn.close()

print("\n" + "="*100)
print("分析")
print("="*100)
print("如果看到某个duplicate_of值有大量记录（>10），很可能是:")
print("  1. API端点在批量处理时出错")
print("  2. 循环中的master_id变量未正确更新")
print("  3. 数据库批量UPDATE时WHERE条件错误")
print("="*100)
