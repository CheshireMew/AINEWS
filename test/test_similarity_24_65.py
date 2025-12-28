#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from crawler.filters.local_deduplicator import LocalDeduplicator

print("="*80)
print("测试ID 24和65的相似度")
print("="*80)

# 获取两条新闻
conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

rows = cursor.execute('''
    SELECT id, title, published_at
    FROM news 
    WHERE id IN (24, 65)
    ORDER BY id
''').fetchall()

if len(rows) < 2:
    print("❌ 找不到这两条新闻")
    sys.exit(1)

title_24 = rows[0][1]
title_65 = rows[1][1]

print(f"\n📰 新闻1 (ID 24):")
print(f"   时间: {rows[0][2]}")
print(f"   标题: {title_24}")

print(f"\n📰 新闻2 (ID 65):")
print(f"   时间: {rows[1][2]}")
print(f"   标题: {title_65}")

conn.close()

# 创建去重器并计算相似度
print("\n" + "="*80)
print("计算相似度")
print("="*80)

deduplicator = LocalDeduplicator(similarity_threshold=0.50)

try:
    similarity = deduplicator.calculate_similarity(title_24, title_65)
    
    print(f"\n🎯 相似度分数: {similarity:.4f}")
    print(f"   当前阈值: 0.50")
    
    if similarity >= 0.50:
        print(f"\n   结果: ✅ 应该被判定为重复")
        print(f"   说明: 相似度 {similarity:.4f} >= 0.50")
    else:
        gap = 0.50 - similarity
        print(f"\n   结果: ❌ 未达到阈值")
        print(f"   差距: {gap:.4f}")
        print(f"   建议阈值: {max(0.40, similarity - 0.01):.2f}")
    
    print("\n" + "="*80)
    print("结论")
    print("="*80)
    
    if similarity >= 0.50:
        print("✓ 算法正确识别了这两条新闻为重复")
        print("✓ 可能是去重时的链式检查阻止了标记")
    else:
        print("✓ 算法未识别为重复（相似度低于阈值）")
        print(f"✓ 需要降低阈值到约 {max(0.40, similarity - 0.01):.2f} 才能识别")
        
except Exception as e:
    print(f"\n❌ 计算失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
