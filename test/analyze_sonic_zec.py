"""分析为什么Sonic和ZEC被判定为重复"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator

# 两条不相关的新闻
news1 = "Sonic 更新 ETF 代币配置方案：仅在 S 价格高于 0.5 美元时执行，发行规模不超 5000 万美元"
news2 = "ZEC上涨突破500 USDT，24H涨幅14.3%"

print("="*100)
print("分析为什么这两条新闻被判定为重复")
print("="*100)
print(f"\n新闻1: {news1}")
print(f"新闻2: {news2}")

dedup = LocalDeduplicator(similarity_threshold=0.50)

# 提取特征
print("\n" + "="*100)
print("特征提取")
print("="*100)

feat1 = dedup.extract_key_features(news1)
feat2 = dedup.extract_key_features(news2)

print(f"\n新闻1特征:")
print(f"  数字: {feat1['numbers']}")
print(f"  关键词: {sorted(list(feat1['keywords']))}")
print(f"  归一化: {feat1['normalized']}")

print(f"\n新闻2特征:")
print(f"  数字: {feat2['numbers']}")
print(f"  关键词: {sorted(list(feat2['keywords']))}")
print(f"  归一化: {feat2['normalized']}")

# 计算相似度
print("\n" + "="*100)
print("相似度计算")
print("="*100)

similarity = dedup.calculate_similarity(news1, news2)
print(f"\n相似度: {similarity:.4f}")
print(f"阈值: 0.50")
print(f"判定结果: {'重复 ❌' if similarity >= 0.50 else '不重复 ✅'}")

# 分析共同特征
common_numbers = feat1['numbers'] & feat2['numbers']
common_keywords = feat1['keywords'] & feat2['keywords']

print(f"\n共同数字: {common_numbers}")
print(f"共同关键词: {sorted(list(common_keywords))}")

print("\n" + "="*100)
print("问题分析")
print("="*100)

if similarity >= 0.50:
    print("❌ 这两条新闻被错误判定为重复")
    print("\n可能的原因:")
    
    if common_numbers:
        print(f"  1. 共享数字: {common_numbers}")
        print(f"     但实际上这些数字的含义完全不同！")
    
    if common_keywords:
        print(f"  2. 共享关键词: {sorted(list(common_keywords))}")
        print(f"     这些可能是通用的财经词汇")
    
    if len(feat1['keywords']) == 0 or len(feat2['keywords']) == 0:
        print(f"  3. 关键词太少，导致误判")
    
    print("\n建议:")
    print("  - 提高相似度阈值（当前0.50可能太低）")
    print("  - 增加实体识别，要求主语相同")
    print("  - 降低通用词汇（如'美元'）的权重")
