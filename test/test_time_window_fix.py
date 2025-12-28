"""测试修复后的时间窗口逻辑"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime, timedelta

print("="*100)
print("测试时间窗口逻辑修复")
print("="*100)

# 创建测试数据：时间跨度很大的新闻
now = datetime.now()
test_news = [
    {
        'id': 1,
        'title': '黄金价格创历史新高',
        'published_at': now - timedelta(hours=48),  # 48小时前
        'source_site': 'test'
    },
    {
        'id': 2,
        'title': 'ZEC价格上涨',
        'published_at': now - timedelta(hours=1),   # 1小时前
        'source_site': 'test'
    },
    {
        'id': 3,
        'title': 'ZEC价格持续上涨',
        'published_at': now - timedelta(minutes=30), # 30分钟前
        'source_site': 'test'
    }
]

print("\n测试数据:")
for news in test_news:
    hours_ago = (now - news['published_at']).total_seconds() / 3600
    print(f"  ID {news['id']}: {news['title']} ({hours_ago:.1f}小时前)")

# 测试：使用time_window_hours=0（处理全部时间）
print("\n" + "="*100)
print("测试：time_window_hours=0 (处理全部新闻)")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=0)
result = dedup.mark_duplicates(test_news)

print("\n结果:")
for news in result:
    is_dup = news.get('is_local_duplicate', False)
    dup_of = news.get('duplicate_of')
    status = "❌ 重复" if is_dup else "✅ 保留"
    print(f"{status} - ID:{news['id']} {news['title']}")
    if is_dup:
        print(f"  duplicate_of: {dup_of}")

print("\n" + "="*100)
print("预期结果:")
print("="*100)
print("  - ID 1 (48小时前) 应该 ✅ 保留 - 距离ID2 和 ID3超过2小时")
print("  - ID 2 和 ID 3 之间可能判定为重复（都是ZEC，时间相近）")
print("\n关键验证:")
print("  - ID 1 不应该和 ID 2/3 比较 (时间差>2小时)")
print("="*100)
