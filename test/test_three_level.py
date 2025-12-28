"""测试三层级链修复"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime

# 模拟三层级场景
test_news = [
    {
        'id': 1,
        'title': '欧盟加密税收报告新规将于2026年1月1日生效',
        'published_at': datetime(2025, 12, 24, 10, 0, 0),
        'source_site': 'test'
    },
    {
        'id': 2,
        'title': '欧盟数字资产税务透明度法案将于2026年1月生效',
        'published_at': datetime(2025, 12, 24, 10, 5, 0),
        'source_site': 'test'
    },
    {
        'id': 3,
        'title': '莱德:美联储2026年降息幅度或有限',
        'published_at': datetime(2025, 12, 24, 10, 10, 0),
        'source_site': 'test'
    }
]

print("="*100)
print("测试三层级链修复")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=0)

# 查看相似度
print("\n相似度矩阵:")
for i in range(len(test_news)):
    for j in range(i+1, len(test_news)):
        sim = dedup.calculate_similarity(test_news[i]['title'], test_news[j]['title'])
        print(f"  ID{test_news[i]['id']} vs ID{test_news[j]['id']}: {sim:.4f}")

result = dedup.mark_duplicates(test_news)

print("\n" + "="*100)
print("去重结果:")
print("="*100)

for news in result:
    is_dup = news.get('is_local_duplicate', False)
    dup_of = news.get('duplicate_of')
    status = "❌ 重复" if is_dup else "✅ 保留"
    print(f"\n{status} - ID:{news['id']}")
    print(f"  标题: {news['title'][:60]}")
    if is_dup:
        print(f"  duplicate_of: {dup_of}")

# 检查是否有三层级
print("\n" + "="*100)
print("验证：是否存在三层级？")
print("="*100)

has_three_level = False
for news in result:
    if news.get('is_local_duplicate'):
        master_id = news.get('duplicate_of')
        # 检查master是否也是重复项
        master = next((n for n in result if n['id'] == master_id), None)
        if master and master.get('is_local_duplicate'):
            print(f"❌ 发现三层级!")
            print(f"  {news['id']} → {master_id} → {master.get('duplicate_of')}")
            has_three_level = True

if not has_three_level:
    print("✅ 没有三层级，修复成功！")

print("="*100)
