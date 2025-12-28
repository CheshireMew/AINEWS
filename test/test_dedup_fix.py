"""测试修复后的去重算法"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime, timedelta

# 创建测试数据
test_news = [
    {
        'id': 101,
        'title': '易理华旗下 Trend Research 今日增持 4.6 万枚 ETH，约合 1.37 亿美元',
        'published_at': datetime.now(),
        'source_site': 'odaily'
    },
    {
        'id': 102,
        'title': '易理华旗下Trend Research增持46,379枚ETH，价值1.37亿美元',
        'published_at': datetime.now(),
        'source_site': 'blockbeats'
    },
    {
        'id': 103,
        'title': 'BTC 突破 10 万美元大关',
        'published_at': datetime.now(),
        'source_site': 'panews'
    },
    {
        'id': 104,
        'title': 'ZEC上涨突破500 USDT，24H涨幅14.3%',
        'published_at': datetime.now() + timedelta(minutes=5),
        'source_site': 'odaily'
    }
]

print("="*100)
print("测试修复后的去重算法")
print("="*100)

# 初始化去重器
dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=24)

# 执行去重标记
result = dedup.mark_duplicates(test_news)

print("\n测试结果:")
print("-"*100)

for news in result:
    is_dup = news.get('is_local_duplicate', False)
    dup_of = news.get('duplicate_of')
    
    status = "❌ 重复" if is_dup else "✅ 保留"
    print(f"\n{status} - ID:{news['id']} - {news['title'][:60]}")
    
    if is_dup:
        print(f"  duplicate_of: {dup_of} (类型: {type(dup_of).__name__})")
        print(f"  原因: {news.get('duplicate_reason', 'N/A')}")
        
        # 🔍 关键验证：duplicate_of 应该是新闻ID（整数），而不是列表索引
        if isinstance(dup_of, int):
            # 检查这个ID是否存在于新闻列表中
            master = next((n for n in result if n['id'] == dup_of), None)
            if master:
                print(f"  ✅ 验证通过: duplicate_of={dup_of} 指向真实新闻ID")
                print(f"     主新闻: {master['title'][:50]}")
            else:
                print(f"  ⚠️ 警告: duplicate_of={dup_of} 无法找到对应新闻")
        else:
            print(f"  ❌ 错误: duplicate_of类型错误，应该是int")

print("\n" + "="*100)

# 统计
stats = dedup.get_dedup_stats(result)
print(f"\n统计信息:")
print(f"  总数: {stats['total']}")
print(f"  唯一: {stats['unique']}")
print(f"  重复: {stats['duplicates']}")
print(f"  去重率: {stats['dedup_rate']}")

print("\n" + "="*100)
print("🎯 预期结果:")
print("  - 新闻101和102应该被识别为重复（ETH增持新闻）")
print("  - 新闻102的duplicate_of应该是101（新闻ID，不是索引0）")
print("  - 新闻103和104应该保留（不重复）")
print("="*100)
