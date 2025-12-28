"""检查并查集逻辑是否正确"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime

# 创建测试场景：A和B相似，C和D相似，但AB和CD不相似
# 如果出现黑洞，可能D会被标记为duplicate_of A

test_news = [
    {
        'id': 100,
        'title': 'Matrixport从Binance提取1090枚BTC',
        'published_at': datetime(2025, 12, 24, 10, 0, 0),
        'source_site': 'test'
    },
    {
        'id': 101,
        'title': 'BTC OG向Binance存入10万枚ETH价值2.92亿美元',
        'published_at': datetime(2025, 12, 24, 10, 5, 0),
        'source_site': 'test'
    },
    {
        'id': 102,
        'title': 'BTC OG向币安存入10万枚ETH价值2.92亿美元',
        'published_at': datetime(2025, 12, 24, 10, 10, 0),
        'source_site': 'test'
    },
    {
        'id': 103,
        'title': '美国失业金人数21.4万人预期22.4万人',
        'published_at': datetime(2025, 12, 24, 10, 15, 0),
        'source_site': 'test'
    }
]

print("="*100)
print("测试并查集逻辑")
print("="*100)

print("\n测试数据:")
for news in test_news:
    print(f"  ID {news['id']}: {news['title']}")

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=0)
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

print("\n" + "="*100)
print("预期结果:")
print("="*100)
print("  - ID 100 (Matrixport BTC): ✅ 保留")
print("  - ID 101 和 102 (BTC OG ETH): 其中一个保留，一个重复")
print("  - ID 103 (失业金): ✅ 保留")
print("\n⚠️ 关键验证:")
print("  - ID 101/102 不应该被标记为 duplicate_of=100")
print("  - ID 103 不应该被标记为重复任何ID")
print("="*100)
