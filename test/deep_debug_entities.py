"""深度调试：检查为什么修复后仍有误判"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator
from datetime import datetime

print("="*100)
print("深度调试：为什么修复后仍有误判")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50, time_window_hours=0)

# 测试案例1：ETH存入 vs BTC提取
title1 = "BTC OG内幕巨鲸向Binance存入10万枚ETH价值2.9212亿美元"
title2 = "Matrixport 5分钟前从Binance提取1090枚比特币"

print("\n【案例1】ETH存入 vs BTC提取")
print(f"标题1: {title1}")
print(f"标题2: {title2}")

# 1. 检查实体提取
entities1 = dedup.extract_entities(title1)
entities2 = dedup.extract_entities(title2)

print(f"\n实体提取:")
print(f"  标题1实体: {entities1}")
print(f"  标题2实体: {entities2}")
print(f"  共同实体: {entities1 & entities2}")

# 2. 检查相似度计算
similarity = dedup.calculate_similarity(title1, title2)
print(f"\n相似度计算:")
print(f"  相似度: {similarity:.4f}")
print(f"  阈值: 0.50")
print(f"  判定: {'重复 ❌' if similarity >= 0.50 else '不重复 ✅'}")

# 3. 如果被判定为重复，分析原因
if similarity >= 0.50:
    print(f"\n❌ 被误判为重复！")
    
    if entities1 & entities2:
        common = entities1 & entities2
        print(f"\n  共同实体: {common}")
        print(f"  ⚠️ 问题：虽然有共同实体（{common}），但这两条新闻完全不同：")
        print(f"     - 一个是存入ETH")
        print(f"     - 一个是提取BTC")
        print(f"\n  实体约束未能阻止误判的原因：")
        print(f"     1. Binance作为交易所，在两条新闻中都出现")
        print(f"     2. 但实体约束只检查'有无共同实体'，没有检查'主要实体是否相同'")
        print(f"     3. 应该检查：ETH vs BTC这样的核心实体是否相同")
    else:
        print(f"\n  ⚠️ 无共同实体但仍被判重复 - 实体检查逻辑可能有bug！")

# 4. 提取关键特征查看
features1 = dedup.extract_key_features(title1)
features2 = dedup.extract_key_features(title2)

print(f"\n关键特征提取:")
print(f"  标题1:")
print(f"    数字: {features1['numbers']}")
print(f"    关键词: {list(features1['keywords'])[:10]}")  # 只显示前10个
print(f"  标题2:")
print(f"    数字: {features2['numbers']}")
print(f"    关键词: {list(features2['keywords'])[:10]}")

print("\n" + "="*100)
print("结论")
print("="*100)

if similarity >= 0.50:
    print("\n问题确认：实体约束逻辑不够严格")
    print("\n当前逻辑：")
    print("  if entities1 and entities2:")
    print("      if not (entities1 & entities2):")
    print("          return 0.0  # 只有在完全没有共同实体时才拦截")
    print("\n改进方案：")
    print("  应该检查'核心实体'（币种/token）是否相同")
    print("  Binance只是'场所实体'，不应作为判断依据")
    print("  应该分离：币种实体(BTC/ETH) vs 场所实体(Binance/Upbit)")
else:
    print("\n✅ 判定正确！实体约束成功阻止了误判")

print("="*100)
