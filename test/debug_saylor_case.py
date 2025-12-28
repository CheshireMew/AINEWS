# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'crawler')
from filters.local_deduplicator import LocalDeduplicator

dedup = LocalDeduplicator(similarity_threshold=0.45, time_window_hours=2)

cases = [
    {
        "name": "Michael Saylor Case",
        "t1": "Michael Saylor再次发布比特币Tracker信息，或暗示再次增持BTC",
        "t2": "Michael Saylor 再次发布比特币 Tracker 信息，或将于下周增持比特币"
    },
    {
        "name": "WLFI Case",
        "t1": "WLFI：已开启治理投票，拟动用财库资金加速 USD1 应用",
        "t2": "WLFI：治理投票正式开启，拟动用金库资金加速USD1应用"
    }
]

for case in cases:
    print(f"\n=== Testing {case['name']} ===")
    t1 = case['t1']
    t2 = case['t2']
    
    f1 = dedup.extract_features(t1)
    f2 = dedup.extract_features(t2)
    
    print(f"Title 1: {t1}")
    print(f"  En: {f1['en_keywords']}")
    print(f"  Zh: {f1['zh_keywords']}")
    print(f"  Num: {f1['numbers']}")
    
    print(f"\nTitle 2: {t2}")
    print(f"  En: {f2['en_keywords']}")
    print(f"  Zh: {f2['zh_keywords']}")
    print(f"  Num: {f2['numbers']}")
    
    sim = dedup.calculate_similarity(f1, f2)
    print(f"\nSimilarity: {sim:.4f}")
    print(f"Threshold: 0.45")
    print(f"Result: {'✅ DUPLICATE' if sim >= 0.45 else '❌ NOT_DUPLICATE'}")
