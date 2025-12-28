"""完整的端到端测试：验证去重修复是否生效"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime

# 创建测试数据 - 模拟真实场景
test_news_list = [
    {
        'id': 10,
        'title': '现货黄金今晨涨破4500美元，创历史新高',
        'published_at': datetime(2025, 12, 27, 12, 0, 0),
        'source_site': 'jinse'
    },
    {
        'id': 1166,
        'title': 'ZEC 24小时涨幅扩大至14.36%，市值升至84.65亿美元',
        'published_at': datetime(2025, 12, 27, 20, 26, 0),
        'source_site': 'blockbeats'
    },
    {
        'id': 1167,
        'title': '「BTC OG内幕巨鲸」已支付313.69万美元资金费率，总浮亏5226万美元',
        'published_at': datetime(2025, 12, 27, 20, 18, 0),
        'source_site': 'blockbeats'
    }
]

print("="*100)
print("完整的端到端测试")
print("="*100)

# 1. 测试LocalDeduplicator
print("\n【步骤1】测试LocalDeduplicator.mark_duplicates()")
print("-"*100)

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=24)
result = dedup.mark_duplicates(test_news_list)

print("\n结果分析:")
for news in result:
    is_dup = news.get('is_local_duplicate', False)
    dup_of = news.get('duplicate_of')
    
    status = "❌ 重复" if is_dup else "✅ 保留"
    print(f"\n{status} - ID:{news['id']}")
    print(f"  标题: {news['title'][:60]}")
    
    if is_dup:
        print(f"  duplicate_of: {dup_of}")
        print(f"  duplicate_of类型: {type(dup_of).__name__}")
        
        # 关键验证
        if isinstance(dup_of, int):
            # 检查是否是真实的新闻ID
            if dup_of in [n['id'] for n in test_news_list]:
                print(f"  ✅ duplicate_of是真实的新闻ID")
            else:
                print(f"  ⚠️ duplicate_of={dup_of}不在新闻列表中 (可能是索引？)")
        else:
            print(f"  ❌ duplicate_of类型错误")

# 2. 检查数据库中的实际值
print("\n" + "="*100)
print("【步骤2】检查数据库中的实际duplicate_of值")
print("-"*100)

import sqlite3
conn = sqlite3.connect('ainews.db')
c = conn.cursor()

c.execute("""
    SELECT id, title, duplicate_of
    FROM news
    WHERE id IN (1166, 1167, 1164, 1162)
    ORDER BY id
""")

print("\n数据库中的值:")
for row in c.fetchall():
    print(f"ID {row[0]}: duplicate_of={row[2]}")
    print(f"  标题: {row[1][:60]}")

conn.close()

print("\n" + "="*100)
print("【结论】")
print("="*100)
print("如果duplicate_of是新闻ID（如10）→ 修复生效")
print("如果duplicate_of是0或很小的数（如0,1,2）→ 修复未生效，仍然是索引")
print("="*100)
