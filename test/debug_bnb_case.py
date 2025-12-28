import sys
sys.path.insert(0, 'crawler')
from filters.local_deduplicator import LocalDeduplicator

dedup = LocalDeduplicator(similarity_threshold=0.45, time_window_hours=1)

title1 = "中国置业投资控股拟购入BNB等数字资产，纳入公司战略储备"
title2 = "中国置业投资控股拟购入 BNB 等数字资产，纳入公司战略储备"

feat1 = dedup.extract_features(title1)
feat2 = dedup.extract_features(title2)

print("\n特征1:")
print(f"  英文关键词: {feat1['en_keywords']}")
print(f"  中文关键词: {feat1['zh_keywords']}")
print(f"  数字: {feat1['numbers']}")

print("\n特征2:")
print(f"  英文关键词: {feat2['en_keywords']}")
print(f"  中文关键词: {feat2['zh_keywords']}")
print(f"  数字: {feat2['numbers']}")

sim = dedup.calculate_similarity(feat1, feat2)
print(f"\n相似度: {sim:.4f}")
print(f"阈值: 0.45")
print(f"判断: {'重复' if sim >= 0.45 else '不重复'} ❌" if sim < 0.45 else "判断: 重复 ✅")
