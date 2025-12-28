"""测试Flow协议修复案例为什么没识别"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator

print("="*100)
print("测试Flow协议修复案例")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50)

titles = [
    "Flow基金会提出的协议修复方案（Mainnet 28）已获得验证者接受并成功部署",
    "Flow：协议修复方案已成功部署，将发布网络上线最终确认信息",
    "Flow基金会提出的协议修复方案已获验证者一致同意并成功部署",
    "Flow：协议修复方案已被网络验证者接受并成功部署，等待生态合作伙伴完成账本同步"
]

print("\n测试的4条标题:")
for i, title in enumerate(titles, 1):
    print(f"{i}. {title}")

print("\n" + "="*100)
print("两两相似度矩阵")
print("="*100)

for i in range(len(titles)):
    for j in range(i+1, len(titles)):
        title1 = titles[i]
        title2 = titles[j]
        
        # 提取特征
        feat1 = dedup.extract_key_features(title1)
        feat2 = dedup.extract_key_features(title2)
        
        # 计算相似度
        similarity = dedup.calculate_similarity(title1, title2)
        
        print(f"\n【{i+1} vs {j+1}】")
        print(f"标题{i+1}: {title1[:50]}...")
        print(f"标题{j+1}: {title2[:50]}...")
        
        print(f"\n关键词{i+1}: {sorted(list(feat1['keywords']))[:10]}")
        print(f"关键词{j+1}: {sorted(list(feat2['keywords']))[:10]}")
        common_kw = feat1['keywords'] & feat2['keywords']
        print(f"共同关键词: {sorted(list(common_kw))[:10]}")
        
        kw_union = feat1['keywords'] | feat2['keywords']
        if kw_union:
            kw_sim = len(common_kw) / len(kw_union)
            print(f"关键词相似度: {kw_sim:.4f}")
        
        print(f"\n数字{i+1}: {feat1['numbers']}")
        print(f"数字{j+1}: {feat2['numbers']}")
        
        print(f"\n最终相似度: {similarity:.4f}")
        print(f"判定: {'✅ 重复' if similarity >= 0.50 else '❌ 不重复'}")
        print("-" * 80)

print("\n" + "="*100)
print("问题分析")
print("="*100)

# 检查是否所有组合都<0.50
max_sim = 0
for i in range(len(titles)):
    for j in range(i+1, len(titles)):
        sim = dedup.calculate_similarity(titles[i], titles[j])
        max_sim = max(max_sim, sim)

if max_sim < 0.50:
    print(f"\n❌ 问题确认：最高相似度{max_sim:.4f} < 0.50")
    print("\n可能原因:")
    print("  1. 关键词权重70%过高，但分词结果不同")
    print("  2. 停用词过滤掉了重要的词（如'方案'、'部署'）")
    print("  3. jieba分词对技术性标题分词不准确")
    print("\n建议:")
    print("  - 降低阈值到0.40-0.45")
    print("  - 或减少停用词")
    print("  - 或调低关键词权重到50-60%，提高字符串序列权重")
else:
    print(f"✅ 最高相似度{max_sim:.4f} >= 0.50，应该会识别")
    print("如果前端没显示，可能是:")
    print("  - 后端未重启")
    print("  - 时间窗口限制")
    print("  - 已被标记过，跳过了")

print("="*100)
