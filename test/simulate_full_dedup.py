"""模拟完整的去重流程 - 使用time_window_hours=0"""
import sys
sys.path.insert(0, '.')

import sqlite3
from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime

print("="*100)
print("模拟用户操作：全部时间（time_window_hours=0）+ 阈值0.50")
print("="*100)

# 1. 从数据库获取真实数据 
conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 获取stage='pending'的新闻（模拟真实场景）
c.execute("""
    SELECT id, title, source_url, source_site, published_at
    FROM news
    WHERE stage = 'pending'
    ORDER BY published_at DESC
    LIMIT 50
""")

news_list = []
for row in c.fetchall():
    news_list.append({
        'id': row[0],
        'title': row[1],
        'source_url': row[2],
        'source_site': row[3],
        'published_at': row[4]
    })

print(f"\n获取了 {len(news_list)} 条pending新闻")

if len(news_list) == 0:
    print("没有pending新闻，退出")
    conn.close()
    exit(0)

print("\n前5条新闻:")
for i, news in enumerate(news_list[:5]):
    print(f"  {i}. ID={news['id']}: {news['title'][:60]}")

# 2. 使用LocalDeduplicator（time_window_hours=0，表示全部时间）
print("\n" + "="*100)
print("执行LocalDeduplicator.mark_duplicates()")
print("  - time_window_hours: 0 (全部时间)")
print("  - similarity_threshold: 0.50")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=0)
marked_news = dedup.mark_duplicates(news_list)

# 3. 分析结果
print("\n结果分析:")
print("-"*100)

duplicates_found = [n for n in marked_news if n.get('is_local_duplicate', False)]
print(f"发现重复项: {len(duplicates_found)} 条")

if len(duplicates_found) > 0:
    print("\n重复项详情（前10条）:")
    for dup in duplicates_found[:10]:
        dup_of = dup.get('duplicate_of')
        print(f"\n  ID {dup['id']}: {dup['title'][:60]}")
        print(f"    duplicate_of: {dup_of} (类型: {type(dup_of).__name__})")
        
        # 检查duplicate_of是否是真实ID
        if isinstance(dup_of, int):
            master = next((n for n in marked_news if n['id'] == dup_of), None)
            if master:
                print(f"    ✅ 指向真实新闻: ID={master['id']}, {master['title'][:40]}...")
            else:
                print(f"    ⚠️ 找不到对应的主新闻 ID={dup_of}")
                # 检查是否是索引
                if dup_of < len(marked_news):
                    try_master = marked_news[dup_of]
                    print(f"    🔍 如果{dup_of}是索引，对应的新闻是: ID={try_master['id']}, {try_master['title'][:40]}...")

conn.close()

print("\n" + "="*100)
print("测试完成")
print("="*100)
