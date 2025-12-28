import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
import json

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 获取黄金新闻
cursor.execute("SELECT id, title FROM news WHERE id = 10")
gold = cursor.fetchone()
print("黄金新闻:")
print(f"  ID {gold[0]}: {gold[1]}\n")

# 获取几条被误判的新闻
print("被误判的新闻:")
problem_ids = [1160, 1161, 1159, 1154]
problem_titles = []
for news_id in problem_ids:
    cursor.execute("SELECT id, title FROM news WHERE id = ?", (news_id,))
    row = cursor.fetchone()
    if row:
        print(f"  ID {row[0]}: {row[1]}")
        problem_titles.append(row[1])

conn.close()

# 现在导入去重模块并测试
from crawler.filters.local_deduplicator import LocalDeduplicator

print("\n" + "="*80)
print("相似度计算测试")
print("="*80)

# 打开文件记录结果
output_file = open('test/dedup_analysis.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg)
    output_file.write(msg + '\n')

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=24)

for i, title in enumerate(problem_titles):
    log(f"\n--- 测试 #{i+1}: {title[:80]} ---" )
    similarity = dedup.calculate_similarity(gold[1], title)
    
    # 提取特征看详细信息
    feat_gold = dedup.extract_key_features(gold[1])
    feat_news = dedup.extract_key_features(title)
    
    log(f"相似度: {similarity:.4f} ({'>=0.50 会被判定为重复!' if similarity >= 0.50 else '<0.50 不会重复'})")
    log(f"黄金数字: {feat_gold['numbers']}")
    log(f"新闻数字: {feat_news['numbers']}")
    log(f"黄金关键词: {sorted(list(feat_gold['keywords']))}")
    log(f"新闻关键词: {sorted(list(feat_news['keywords']))}")

output_file.close()
print("\n结果已保存到 test/dedup_analysis.txt")
