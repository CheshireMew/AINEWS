"""调试本地去重算法"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from filters.local_deduplicator import LocalDeduplicator

dedup = LocalDeduplicator(similarity_threshold=0.7)

title1 = '易理华旗下 Trend Research 今日增持 4.6 万枚 ETH，约合 1.37 亿美元'
title2 = '易理华旗下Trend Research增持46,379枚ETH，价值1.37亿美元'

print("=" * 80)
print("标题1:", title1)
print("标题2:", title2)
print("=" * 80)

features1 = dedup.extract_key_features(title1)
features2 = dedup.extract_key_features(title2)

print("\n特征1:")
print(f"  数字: {features1['numbers']}")
print(f"  关键词: {features1['keywords']}")
print(f"  标准化: {features1['normalized']}")

print("\n特征2:")
print(f"  数字: {features2['numbers']}")
print(f"  关键词: {features2['keywords']}")
print(f"  标准化: {features2['normalized']}")

print("\n交集分析:")
print(f"  数字交集: {features1['numbers'] & features2['numbers']}")
print(f"  关键词交集: {features1['keywords'] & features2['keywords']}")

sim = dedup.calculate_similarity(title1, title2)
print(f"\n最终相似度: {sim:.3f}")
print(f"阈值: {dedup.similarity_threshold}")
print(f"判定: {'✅ 重复' if sim >= dedup.similarity_threshold else '❌ 不重复'}")
