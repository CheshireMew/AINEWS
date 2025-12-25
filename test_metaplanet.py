
import sys
import os
import logging

sys.path.insert(0, os.path.abspath('crawler'))

from filters.local_deduplicator import LocalDeduplicator

def test_metaplanet():
    # Suppress Jieba logging
    jieba_logger = logging.getLogger('jieba')
    jieba_logger.setLevel(logging.ERROR)

    titles = [
        "Metaplanet 董事会批准增持比特币计划",
        "Metaplanet 董事会批准增持比特币计划，拟在 2027 年底前持有 21 万枚 BTC",
        "Metaplanet董事会批准扩大比特币购买计划"
    ]
    
    dedup = LocalDeduplicator(similarity_threshold=0.50)
    
    # Save output to file
    with open('score_metaplanet.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        
        for i in range(len(titles)):
            for j in range(i + 1, len(titles)):
                t1 = titles[i]
                t2 = titles[j]
                
                print("-" * 50)
                print(f"Compare T{i+1} vs T{j+1}:")
                # print(f"  T{i+1}: {t1}")
                # print(f"  T{j+1}: {t2}")
                
                feat1 = dedup.extract_key_features(t1)
                feat2 = dedup.extract_key_features(t2)
                
                # print(f"  Norm 1: {feat1['normalized']}")
                # print(f"  Norm 2: {feat2['normalized']}")
                print(f"  KWs 1: {feat1['keywords']}")
                print(f"  KWs 2: {feat2['keywords']}")
                print(f"  Nums 1: {feat1['numbers']}")
                print(f"  Nums 2: {feat2['numbers']}")
                
                score = dedup.calculate_similarity(t1, t2)
                print(f"  Score: {score:.4f}")
                print(f"  Result: {'MATCH' if score >= dedup.similarity_threshold else 'NO MATCH'}")

    sys.stdout = sys.__stdout__
    print("Test finished. Check score_metaplanet.txt")

if __name__ == "__main__":
    test_metaplanet()
