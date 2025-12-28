"""分析新的黑洞案例"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator

print("="*100)
print("分析新的黑洞案例")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50)

# 案例1：ETH vs BTC
case1_news1 = "「BTC OG内幕巨鲸」向Binance存入10万枚ETH，价值2.9212亿美元"
case1_news2 = "Matrixport 5分钟前从Binance提取1090枚比特币"

print("\n【案例1】ETH存入 vs BTC提取")
print(f"新闻1: {case1_news1}")
print(f"新闻2: {case1_news2}")

entities1 = dedup.extract_entities(case1_news1)
entities2 = dedup.extract_entities(case1_news2)
similarity1 = dedup.calculate_similarity(case1_news1, case1_news2)

print(f"\n实体1: {entities1}")
print(f"实体2: {entities2}")
print(f"共同实体: {entities1 & entities2}")
print(f"相似度: {similarity1:.4f}")
print(f"判定: {'重复 ❌' if similarity1 >= 0.50 else '不重复 ✅'}")

# 案例2：失业金 vs 比特币
case2_news1 = "美国至12月20日当周初请失业金人数21.4万人，预期22.4万人"
case2_news2 = "Metaplanet 董事会批准增持比特币计划"

print("\n" + "="*100)
print("【案例2】美国失业金 vs 比特币增持")
print(f"新闻1: {case2_news1}")
print(f"新闻2: {case2_news2}")

entities3 = dedup.extract_entities(case2_news1)
entities4 = dedup.extract_entities(case2_news2)
similarity2 = dedup.calculate_similarity(case2_news1, case2_news2)

print(f"\n实体1: {entities3}")
print(f"实体2: {entities4}")
print(f"共同实体: {entities3 & entities4}")
print(f"相似度: {similarity2:.4f}")
print(f"判定: {'重复 ❌' if similarity2 >= 0.50 else '不重复 ✅'}")

print("\n" + "="*100)
print("问题分析")
print("="*100)

if similarity1 >= 0.50:
    print("\n❌ 案例1被误判为重复")
    if entities1 & entities2:
        print(f"  共同实体: {entities1 & entities2}")
        print("  问题：虽然有共同实体（如Binance、BTC、ETH），但操作完全不同（存入vs提取）")
    else:
        print("  ⚠️ 无共同实体但仍被判重复 - 实体检查可能未生效！")

if similarity2 >= 0.50:
    print("\n❌ 案例2被误判为重复") 
    if entities3 & entities4:
        print(f"  共同实体: {entities3 & entities4}")
   else:
        print("  ⚠️ 无共同实体但仍被判重复 - 实体检查可能未生效！")

print("\n可能的原因:")
print("  1. 后端未重启，仍在运行旧代码")
print("  2. 实体约束逻辑有bug")
print("  3. Binance被识别为共同实体，但应该考虑操作方向（存入vs提取）")
print("="*100)
