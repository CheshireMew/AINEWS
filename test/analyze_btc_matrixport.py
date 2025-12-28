"""分析比特币观点 vs Matrixport提取误判"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator

title1 = "观点：若考虑通胀因素，比特币仍未突破10万美元"
title2 = "Matrixport 5分钟前从Binance提取1090枚比特币"

print("="*100)
print("分析新误判案例")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50)

print(f"\n标题1: {title1}")
print(f"\n标题2: {title2}")

# 1. 检查实体
entities1 = dedup.extract_entities(title1)
entities2 = dedup.extract_entities(title2)

print(f"\n实体1: {entities1}")
print(f"实体2: {entities2}")
print(f"共同实体: {entities1 & entities2}")

# 2. 检查特征
feat1 = dedup.extract_key_features(title1)
feat2 = dedup.extract_key_features(title2)

print(f"\n特征1:")
print(f"  数字: {feat1['numbers']}")
print(f"  关键词前10: {list(feat1['keywords'])[:10]}")

print(f"\n特征2:")
print(f"  数字: {feat2['numbers']}")
print(f"  关键词前10: {list(feat2['keywords'])[:10]}")

print(f"\n共同数字: {feat1['numbers'] & feat2['numbers']}")
print(f"共同关键词: {sorted(list(feat1['keywords'] & feat2['keywords']))[:10]}")

# 3. 计算相似度
similarity = dedup.calculate_similarity(title1, title2)

print(f"\n相似度: {similarity:.4f}")
print(f"阈值: 0.50")
print(f"判定: {'重复 ❌' if similarity >= 0.50 else '不重复 ✅'}")

if similarity >= 0.50:
    print(f"\n❌ 被误判为重复！")
    print(f"\n分析:")
    print(f"  - 两条新闻主题完全不同：价格观点 vs 转账动作")
    print(f"  - 共同实体只有'比特币'，但这是币圈新闻的通用主题")
    print(f"  - 可能原因：")
    print(f"    1. '比特币'这个词权重过高")
    print(f"    2. 数字匹配给了额外分数")
    print(f"    3. 阈值0.50可能太低")
    print(f"\n建议：")
    print(f"  - 将阈值提高到0.60或0.65")
    print(f"  - 或者要求不仅有共同实体，还要有更多共同关键词")

print("="*100)
