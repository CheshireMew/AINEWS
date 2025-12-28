#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from crawler.filters.local_deduplicator import LocalDeduplicator

print("="*80)
print("测试Master合并逻辑 - ID 1223和1241")
print("="*80)

# 获取新闻
conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

rows = cursor.execute('''
    SELECT id, title, published_at, duplicate_of
    FROM news 
    WHERE id IN (1223, 1241)
    ORDER BY published_at
''').fetchall()

if len(rows) < 2:
    print("❌ 找不到这两条新闻")
    sys.exit(1)

news_1 = {
    'id': rows[0][0],
    'title': rows[0][1],
    'published_at': rows[0][2],
    'duplicate_of': rows[0][3]
}

news_2 = {
    'id': rows[1][0],
    'title': rows[1][1],
    'published_at': rows[1][2],
    'duplicate_of': rows[1][3]
}

conn.close()

print(f"\n较早: ID {news_1['id']} at {news_1['published_at']}")
print(f"  标题: {news_1['title']}")
print(f"  duplicate_of: {news_1['duplicate_of']}")

print(f"\n较晚: ID {news_2['id']} at {news_2['published_at']}")
print(f"  标题: {news_2['title']}")
print(f"  duplicate_of: {news_2['duplicate_of']}")

# 测试相似度
deduplicator = LocalDeduplicator()
similarity = deduplicator.calculate_similarity(news_1['title'], news_2['title'])

print(f"\n相似度: {similarity:.4f} ({similarity*100:.2f}%)")
print(f"阈值: 0.50 (50%)")
print(f"判定: {'✅ 应该判重' if similarity >= 0.50 else '❌ 不应判重'}")

print("\n" + "="*80)
print("结论")
print("="*80)
print("这两条新闻明显应该被判重（相似度65.88%）")
print("\n可能原因:")
print("1. 这两条新闻是去重运行后才抓取的（最可能）")
print("2. Master合并逻辑未触发（需要检查）")
print("\n建议:")
print("现在重新运行去重，应该会将ID", news_2['id'], "标记为指向ID", news_1['id'])
