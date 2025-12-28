# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'crawler')
from filters.local_deduplicator import LocalDeduplicator

# 测试去重器是否正常工作
dedup = LocalDeduplicator(similarity_threshold=0.45, time_window_hours=2)

test_news = [
    {"id": 1, "title": "BTC突破88000美元", "published_at": "2025-12-26 10:00:00"},
    {"id": 2, "title": "ETH跌破2900美元", "published_at": "2025-12-26 10:05:00"},
]

print("测试去重功能...")
print(f"输入新闻数: {len(test_news)}")

try:
    result = dedup.mark_duplicates(test_news)
    print(f"输出新闻数: {len(result)}")
    for news in result:
        print(f"  ID {news['id']}: is_duplicate={news.get('is_local_duplicate')}, duplicate_of={news.get('duplicate_of')}")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
