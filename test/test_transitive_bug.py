"""测试并查集传递性问题"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime

# 构造场景：A和B相似，B和C相似，但A和C不相似
test_news = [
    {
        'id': 1,
        'title': 'Matrixport从Binance提取1090枚BTC',
        'published_at': datetime(2025, 12, 24, 10, 0, 0),
        'source_site': 'test'
    },
    {
        'id': 2,
        'title': 'Matrixport从币安提取1090枚比特币',  # 和1相似
        'published_at': datetime(2025, 12, 24, 10, 5, 0),
        'source_site': 'test'
    },
    {
        'id': 3,
        'title': 'Binance比特币提取活动增加',  # 和2有点像，但和1不像
        'published_at': datetime(2025, 12, 24, 10, 10, 0),
        'source_site': 'test'
    },
    {
        'id': 4,
        'title': 'BTC OG向Binance存入10万枚ETH',  # 和3有点像（都有Binance），但和1完全不像
        'published_at': datetime(2025, 12, 24, 10, 15, 0),
        'source_site': 'test'
    }
]

print("="*100)
print("测试并查集传递性问题")
print("="*100)

print("\n测试数据:")
for news in test_news:
    print(f"  ID {news['id']}: {news['title']}")

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=0)

# 先看看实际的相似度
print("\n实际相似度矩阵:")
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
    print(f"  标题: {news['title']}")
    if is_dup:
        print(f"  duplicate_of: {dup_of}")
        print(f"  ⚠️ 检查: ID{news['id']}和ID{dup_of}是否真的相似？")

print("\n" + "="*100)
print("问题诊断")
print("="*100)
print("如果ID4被标记为duplicate_of=1，但它们完全不相似")
print("→ 证明并查集的传递性导致了黑洞效应！")
print("="*100)
