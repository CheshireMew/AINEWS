
import sys
import os
import logging

# Ensure we can import from crawler
sys.path.insert(0, os.path.abspath('crawler'))

from filters.local_deduplicator import LocalDeduplicator

def test_cz():
    # Suppress Jieba logging
    jieba_logger = logging.getLogger('jieba')
    jieba_logger.setLevel(logging.ERROR)

    t1 = "CZ：Binance钱包已支持识别恶意地址，尝试向其转账将会收到警告"
    t2 = "CZ：加密行业应根除地址投毒攻击，币安已支持识别恶意地址"
    
    dedup = LocalDeduplicator(similarity_threshold=0.60)
    
    print("Testing CZ Case:")
    
    # Save output to file
    with open('score_cz.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        
        print("-" * 50)
        print(f"T1: {t1}")
        print(f"T2: {t2}")
        
        feat1 = dedup.extract_key_features(t1)
        feat2 = dedup.extract_key_features(t2)
        
        print(f"KWs 1: {feat1['keywords']}")
        print(f"KWs 2: {feat2['keywords']}")
        print(f"Norm 1: {feat1['normalized']}")
        print(f"Norm 2: {feat2['normalized']}")
        
        score = dedup.calculate_similarity(t1, t2)
        print(f"Score: {score:.4f}")
        print(f"Result: {'MATCH' if score >= dedup.similarity_threshold else 'NO MATCH'}")

    sys.stdout = sys.__stdout__
    print("Test finished. Check score_cz.txt")

if __name__ == "__main__":
    test_cz()
