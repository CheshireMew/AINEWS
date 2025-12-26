import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 检查 48 小时内各阶段的数据数量
cutoff = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
print(f"Cutoff time (48h ago): {cutoff}\n")

# deduplicated_news 表的各阶段统计
print("=== deduplicated_news 表统计 ===")
cursor.execute("""
    SELECT stage, COUNT(*) 
    FROM deduplicated_news 
    WHERE deduplicated_at >= ? 
    GROUP BY stage
""", (cutoff,))
for row in cursor.fetchall():
    print(f"  stage={row[0]}: {row[1]} 条")

# 特别检查：有多少是 stage='deduplicated' 的（即待过滤的）
cursor.execute("""
    SELECT COUNT(*) 
    FROM deduplicated_news 
    WHERE deduplicated_at >= ? AND stage = 'deduplicated'
""", (cutoff,))
dedup_pending = cursor.fetchone()[0]
print(f"\n  ★ 待过滤的 (stage='deduplicated'): {dedup_pending} 条")

# curated_news 表统计
print("\n=== curated_news 表统计 ===")
cursor.execute("""
    SELECT COUNT(*) 
    FROM curated_news 
    WHERE curated_at >= ?
""", (cutoff,))
curated_total = cursor.fetchone()[0]
print(f"  总数: {curated_total} 条")

# 检查黑名单
print("\n=== 黑名单关键词 ===")
cursor.execute("SELECT keyword, match_type FROM keyword_blacklist")
keywords = cursor.fetchall()
if keywords:
    for kw in keywords:
        print(f"  - {kw[0]} ({kw[1]})")
else:
    print("  ⚠️ 黑名单为空！")

conn.close()
