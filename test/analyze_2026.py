"""分析2026误判原因"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator

title1 = "CNBC：Kraken 计划于 2026 年推出预测市场服务"
title2 = "机构：美国2026年仍存在约3次降息空间"

print("="*100)
print("分析2026误判原因")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50)

print(f"\n标题1: {title1}")
print(f"标题2: {title2}")

# 提取特征
feat1 = dedup.extract_key_features(title1)
feat2 = dedup.extract_key_features(title2)

print(f"\n特征1:")
print(f"  数字: {feat1['numbers']}")
print(f"  关键词: {list(feat1['keywords'])[:15]}")

print(f"\n特征2:")
print(f"  数字: {feat2['numbers']}")
print(f"  关键词: {list(feat2['keywords'])[:15]}")

print(f"\n共同数字: {feat1['numbers'] & feat2['numbers']}")
print(f"共同关键词: {feat1['keywords'] & feat2['keywords']}")

# 计算相似度
similarity = dedup.calculate_similarity(title1, title2)
print(f"\n最终相似度: {similarity:.4f}")
print(f"阈值: 0.50")
print(f"判定: {'重复 ❌' if similarity >= 0.50 else '不重复 ✅'}")

if similarity >= 0.50:
    print(f"\n❌ 被误判！")
    print(f"\n问题分析:")
    print(f"  - 共同数字'2026'作为年份，权重过高")
    print(f"  - 年份数字(>2000)应该被视为'弱特征'，降低权重或完全排除")
    print(f"\n建议:")
    print(f"  1. 过滤年份数字(2000-2030)")
    print(f"  2. 或降低单一数字匹配的权重")
