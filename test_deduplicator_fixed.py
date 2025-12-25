
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from crawler.filters.local_deduplicator import LocalDeduplicator

def test_fix():
    print("Testing Updated Deduplicator...")
    deduper = LocalDeduplicator()
    
    t1 = "Metaplanet董事会批准增持比特币计划"
    t2 = "Metaplanet 董事会批准增持比特币计划，拟在 2027 年底前持有 21 万枚 BTC"
    
    score = deduper.calculate_similarity(t1, t2)
    print(f"Title 1: {t1}")
    print(f"Title 2: {t2}")
    print(f"Similarity Score: {score}")
    
    if score >= 0.9:
        print("✅ SUCCESS: High similarity detected via inclusion logic")
    else:
        print(f"❌ FAILURE: Score {score} is too low")
        
    # 测试数字冲突情况
    t3 = "Metaplanet董事会批准增持100枚比特币"
    t4 = "Metaplanet董事会批准增持200枚比特币"
    score_conflict = deduper.calculate_similarity(t3, t4)
    print(f"\nConflict Test: {t3} vs {t4}")
    print(f"Score: {score_conflict}")
    if score_conflict < 0.9:
         print("✅ SUCCESS: Conflict detected, low score returned")
    else:
         print("❌ FAILURE: Conflict ignored, high score returned")

if __name__ == "__main__":
    test_fix()
