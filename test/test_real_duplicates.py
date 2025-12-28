"""测试真实重复案例为什么没被识别"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator

print("="*100)
print("测试真实重复案例")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50)

# 测试案例1：Polymarket黑客
title1 = "Polymarket：近期用户账户遭黑客攻击事件系第三方漏洞所致"
title2 = "Polymarket确认用户账户遭黑客攻击，源于第三方认证漏洞"

print("\n【案例1】Polymarket黑客")
print(f"标题1: {title1}")
print(f"标题2: {title2}")

# 检查实体
entities1 = dedup.extract_entities(title1)
entities2 = dedup.extract_entities(title2)
print(f"\n实体1: {entities1}")
print(f"实体2: {entities2}")
print(f"共同实体: {entities1 & entities2}")

# 检查特征
feat1 = dedup.extract_key_features(title1)
feat2 = dedup.extract_key_features(title2)
print(f"\n关键词1: {list(feat1['keywords'])[:10]}")
print(f"关键词2: {list(feat2['keywords'])[:10]}")
print(f"共同关键词: {sorted(list(feat1['keywords'] & feat2['keywords']))}")
print(f"关键词相似度: {len(feat1['keywords'] & feat2['keywords']) / len(feat1['keywords'] | feat2['keywords']):.4f}")

# 计算相似度
similarity = dedup.calculate_similarity(title1, title2)
print(f"\n最终相似度: {similarity:.4f}")
print(f"阈值: 0.50")
print(f"判定: {'✅ 重复' if similarity >= 0.50 else '❌ 不重复'}")

# 测试案例2：Trust Wallet
print("\n" + "="*100)
print("【案例2】Trust Wallet赔付")
title3 = "CZ：Trust Wallet将全额承担黑客事件损失，用户资金安全无虞"
title4 = "CZ：Trust Wallet 将全额赔付用户资金损失"

print(f"标题3: {title3}")
print(f"标题4: {title4}")

similarity2 = dedup.calculate_similarity(title3, title4)
print(f"\n相似度: {similarity2:.4f}")
print(f"判定: {'✅ 重复' if similarity2 >= 0.50 else '❌ 不重复'}")

# 测试案例3：FLOW闪崩
print("\n" + "="*100)
print("【案例3】FLOW闪崩")
title5 = "FLOW短时跌破0.125美元，24H跌幅超42%"
title6 = "FLOW「闪崩」跌超42%，市值跌至1.65亿美元"

print(f"标题5: {title5}")
print(f"标题6: {title6}")

similarity3 = dedup.calculate_similarity(title5, title6)
print(f"\n相似度: {similarity3:.4f}")
print(f"判定: {'✅ 重复' if similarity3 >= 0.50 else '❌ 不重复'}")

print("\n" + "="*100)
if similarity < 0.50 or similarity2 < 0.50 or similarity3 < 0.50:
    print("❌ 问题确认：算法无法识别明显的重复！")
    print("\n可能原因:")
    print("  1. 关键词权重过高导致数字/实体匹配被忽略")
    print("  2. 我之前降低数字权重太多了")
    print("  3. 需要重新平衡各项权重")
else:
    print("✅ 算法能正确识别这些重复")
print("="*100)
