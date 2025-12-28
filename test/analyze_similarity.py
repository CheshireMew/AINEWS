import sys
sys.path.append('.')

from crawler.filters.local_deduplicator import LocalDeduplicator
import sqlite3

# 获取两条新闻
conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()
rows = cursor.execute('''
    SELECT id, title, content, published_at 
    FROM news 
    WHERE id IN (24, 65)
    ORDER BY id
''').fetchall()

news_24 = {
    'id': rows[0][0],
    'title': rows[0][1],
    'content': rows[0][2],
    'published_at': rows[0][3]
}

news_65 = {
    'id': rows[1][0],
    'title': rows[1][1],
    'content': rows[1][2],
    'published_at': rows[1][3]
}

conn.close()

print("="*80)
print("分析两条新闻的相似度")
print("="*80)

print(f"\n新闻1 (ID {news_24['id']}):")
print(f"  标题: {news_24['title']}")
print(f"  时间: {news_24['published_at']}")

print(f"\n新闻2 (ID {news_65['id']}):")
print(f"  标题: {news_65['title']}")
print(f"  时间: {news_65['published_at']}")

# 创建去重器并计算相似度
deduplicator = LocalDeduplicator(threshold=0.50)

# 计算相似度
similarity = deduplicator.calculate_similarity(news_24, news_65)

print(f"\n相似度计算结果: {similarity:.4f}")
print(f"阈值设置: 0.50")

if similarity >= 0.50:
    print("✅ 应该被判定为重复")
else:
    print(f"❌ 未达到阈值，差距: {0.50 - similarity:.4f}")

print("\n" + "="*80)
print("分析为什么可能没被判定为重复")
print("="*80)

# 检查它们的发布时间差
from datetime import datetime
try:
    time_24 = datetime.fromisoformat(news_24['published_at'].replace('Z', '+00:00'))
    time_65 = datetime.fromisoformat(news_65['published_at'].replace('Z', '+00:00'))
    time_diff = abs((time_24 - time_65).total_seconds() / 3600)
    print(f"时间差: {time_diff:.2f} 小时")
    print(f"时间窗口设置: 通常是固定的（比如0小时，即全量对比）")
except Exception as e:
    print(f"时间解析失败: {e}")
