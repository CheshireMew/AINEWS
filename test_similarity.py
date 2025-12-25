from difflib import SequenceMatcher

title1 = "Wintermute CEO：部分宣称「退出加密」的年轻建设者和KOL其实从未真正入场，谈不上「退出」"
title2 = "Wintermute CEO：30岁以下宣布退圈的加密开发者与KOL均为骗子"

ratio = SequenceMatcher(None, title1, title2).ratio()

print(f"标题1: {title1}")
print(f"标题2: {title2}")
print(f"\n相似度: {ratio:.2%}")
print(f"阈值: 50%")
print(f"\n结果: {'✅ 会被去重' if ratio >= 0.50 else '❌ 不会被去重'}")
