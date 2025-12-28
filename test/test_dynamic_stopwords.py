# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'crawler')
from filters.local_deduplicator import LocalDeduplicator

dedup = LocalDeduplicator(similarity_threshold=0.45, time_window_hours=2)

# 测试1：BNB购入（非价格新闻，应该识别为重复）
title1 = "中国置业投资控股拟购入BNB等数字资产，纳入公司战略储备"
title2 = "中国置业投资控股拟购入 BNB 等数字资产，纳入公司战略储备"

feat1 = dedup.extract_features(title1)
feat2 = dedup.extract_features(title2)
sim1 = dedup.calculate_similarity(feat1, feat2)

print("测试1: BNB购入新闻")
print(f"  标题1: {title1}")
print(f"  标题2: {title2}")
print(f"  相似度: {sim1:.4f}")
print(f"  结果: {'✅ DUPLICATE' if sim1 >= 0.45 else '❌ NOT duplicate'}")

# 测试2：价格新闻（包含"美元"，应该不重复）
title3 = "BTC突破88000美元，日内涨幅0.72%"
title4 = "ETH跌破2900美元，日内下跌2.09%"

feat3 = dedup.extract_features(title3)
feat4 = dedup.extract_features(title4)
sim2 = dedup.calculate_similarity(feat3, feat4)

print("\n测试2: 价格新闻")
print(f"  标题3: {title3}")
print(f"  标题4: {title4}")
print(f"  相似度: {sim2:.4f}")
print(f"  结果: {'❌ DUPLICATE (误判)' if sim2 >= 0.45 else '✅ NOT duplicate'}")
