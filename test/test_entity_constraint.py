"""测试实体约束是否生效"""
import sys
sys.path.insert(0, '.')

from crawler.filters.local_deduplicator import LocalDeduplicator

print("="*100)
print("测试实体约束功能")
print("="*100)

dedup = LocalDeduplicator(similarity_threshold=0.50)

# 测试用例
test_cases = [
    {
        'title1': 'Sonic 更新 ETF 代币配置方案：仅在 S 价格高于 0.5 美元时执行，发行规模不超 5000 万美元',
        'title2': 'ZEC上涨突破500 USDT，24H涨幅14.3%',
        'expected': '不重复',
        'reason': 'Sonic vs ZEC - 完全不同的实体'
    },
    {
        'title1': 'BTC突破10万美元大关',
        'title2': 'ETH价格下跌5%',
        'expected': '不重复',
        'reason': 'BTC vs ETH - 不同币种'
    },
    {
        'title1': '慢雾：Debot风险钱包用户私钥被盗，黑客目前获利25.5万美元资产',
        'title2': '慢雾余弦：DeBot 相关用户私钥被盗，黑客目前获利 25.5 万美元资产并在持续盗窃',
        'expected': '重复',
        'reason': '慢雾+DeBot - 相同实体，内容高度相似'
    },
    {
        'title1': 'Flow 基金会正在调查可能影响 Flow 网络的安全事件',
        'title2': 'Flow基金会正调查可能影响Flow网络的安全事件',
        'expected': '重复',
        'reason': 'Flow - 相同实体，内容几乎一致'
    },
    {
        'title1': 'Andrew Tate涉嫌参与加密洗钱活动，过去两年已向Railgun存入3000万美元',
        'title2': '分析师：Andrew Tate 涉嫌参与加密洗钱活动，过去两年已向 Railgun 存入 3000 万美元',
        'expected': '重复',
        'reason': 'Andrew Tate+Railgun - 相同实体和事件'
    }
]

print("\n测试结果:")
print("="*100)

passed = 0
failed = 0

for i, case in enumerate(test_cases, 1):
    print(f"\n【测试 {i}】{case['reason']}")
    print(f"  新闻1: {case['title1'][:70]}...")
    print(f"  新闻2: {case['title2'][:70]}...")
    
    # 提取实体
    entities1 = dedup.extract_entities(case['title1'])
    entities2 = dedup.extract_entities(case['title2'])
    print(f"  实体1: {entities1}")
    print(f"  实体2: {entities2}")
    print(f"  共同实体: {entities1 & entities2}")
    
    # 计算相似度
    similarity = dedup.calculate_similarity(case['title1'], case['title2'])
    print(f"  相似度: {similarity:.4f}")
    
    # 判定结果
    is_duplicate = similarity >= 0.50
    actual = '重复' if is_duplicate else '不重复'
    
    if actual == case['expected']:
        print(f"  ✅ 结果：{actual} (符合预期)")
        passed += 1
    else:
        print(f"  ❌ 结果：{actual} (预期：{case['expected']})")
        failed += 1

print("\n" + "="*100)
print(f"测试统计: {passed} 通过, {failed} 失败")
print("="*100)

if failed == 0:
    print("🎉 所有测试通过！实体约束功能正常工作。")
else:
    print(f"⚠️ 有 {failed} 个测试未通过，需要调整。")
