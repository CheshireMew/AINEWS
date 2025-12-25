
import sys
import os
import logging

sys.path.insert(0, os.path.abspath('crawler'))

from filters.local_deduplicator import LocalDeduplicator

def test_vitalik():
    # Suppress Jieba logging
    jieba_logger = logging.getLogger('jieba')
    jieba_logger.setLevel(logging.ERROR)

    titles = [
        "Vitalik Buterin 预测 2030 年代将出现无 bug 代码",
        "Vitalik预测：2030年代无Bug代码将成为可能"
    ]
    
    dedup = LocalDeduplicator(similarity_threshold=0.50)
    
    # Save output to file
    with open('score_vitalik.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        
        t1 = titles[0]
        t2 = titles[1]
        
        print("-" * 50)
        print(f"Compare T1 vs T2:")
        print(f"  T1: {t1}")
        print(f"  T2: {t2}")
        
        feat1 = dedup.extract_key_features(t1)
        feat2 = dedup.extract_key_features(t2)
        
        print(f"  KWs 1: {feat1['keywords']}")
        print(f"  KWs 2: {feat2['keywords']}")
        print(f"  Nums 1: {feat1['numbers']}")
        print(f"  Nums 2: {feat2['numbers']}")
        
        score = dedup.calculate_similarity(t1, t2)
        print(f"  Score: {score:.4f}")
        print(f"  Result: {'MATCH' if score >= dedup.similarity_threshold else 'NO MATCH'}")

    sys.stdout = sys.__stdout__
    print("Test finished. Check score_vitalik.txt")

if __name__ == "__main__":
    test_vitalik()
