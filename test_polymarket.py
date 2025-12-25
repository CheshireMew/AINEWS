
import sys
import os
import logging

# Ensure we can import from crawler
sys.path.insert(0, os.path.abspath('crawler'))

from filters.local_deduplicator import LocalDeduplicator

def test_polymarket():
    # Suppress Jieba logging
    jieba_logger = logging.getLogger('jieba')
    jieba_logger.setLevel(logging.ERROR)

    titles = [
        "Polymarket确认用户账户遭黑客攻击，源于第三方认证漏洞",
        "Polymarket确认遭第三方认证漏洞攻击，部分用户资金被盗",
        "Polymarket证实近期用户账户遭黑客攻击系第三方漏洞所致",
        "Polymarket：近期用户账户遭黑客攻击事件系第三方漏洞所致"
    ]
    
    dedup = LocalDeduplicator(similarity_threshold=0.65)
    
    print("Testing Polymarket Cases:")
    
    # Save output to file to avoid truncation issues
    with open('score_polymarket.txt', 'w', encoding='utf-8') as f:
        sys.stdout = f
        
        for i in range(len(titles)):
            for j in range(i + 1, len(titles)):
                t1 = titles[i]
                t2 = titles[j]
                
                print("-" * 50)
                print(f"Compare T{i+1} vs T{j+1}:")
                print(f"  T{i+1}: {t1}")
                print(f"  T{j+1}: {t2}")
                
                feat1 = dedup.extract_key_features(t1)
                feat2 = dedup.extract_key_features(t2)
                
                print(f"  KWs 1: {feat1['keywords']}")
                print(f"  KWs 2: {feat2['keywords']}")
                
                score = dedup.calculate_similarity(t1, t2)
                print(f"  Score: {score:.4f}")
                
                print(f"  Result: {'MATCH' if score >= dedup.similarity_threshold else 'NO MATCH'}")

    sys.stdout = sys.__stdout__
    print("Test finished. Check score_polymarket.txt")

if __name__ == "__main__":
    test_polymarket()
