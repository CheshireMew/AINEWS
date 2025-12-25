
import sys
import os

# Ensure we can import from crawler
sys.path.insert(0, os.path.abspath('crawler'))

from filters.local_deduplicator import LocalDeduplicator

def test_similarity():
    # User Case
    title1 = "Aave 创始人千万美元购币被指控疑似操纵治理投票"
    title2 = "Aave创始人因增持1000万美元AAVE代币，被指旨在增强治理投票权"
    
    dedup = LocalDeduplicator(similarity_threshold=0.65)
    
    # Suppress Jieba logging
    import logging
    jieba_logger = logging.getLogger('jieba')
    jieba_logger.setLevel(logging.ERROR)
    
    # Capture output to file
    with open('score.txt', 'w', encoding='utf-8') as f:
        # Redirect stdout
        sys.stdout = f
        
        print("-" * 50)
        print(f"Title 1: {title1}")
        print(f"Title 2: {title2}")
        
        # Extract features to see what's happening
        feat1 = dedup.extract_key_features(title1)
        feat2 = dedup.extract_key_features(title2)
        
        print(f"\nFeatures 1:")
        print(f"  Numbers: {feat1['numbers']}")
        print(f"  Keywords: {feat1['keywords']}")
        print(f"  Norm: {feat1['normalized']}")
        
        print(f"\nFeatures 2:")
        print(f"  Numbers: {feat2['numbers']}")
        print(f"  Keywords: {feat2['keywords']}")
        print(f"  Norm: {feat2['normalized']}")
        
        score = dedup.calculate_similarity(title1, title2)
        print(f"\nSimilarity Score: {score}")
        
        if score >= dedup.similarity_threshold:
            print("Result: DUPLICATE (Match)")
        else:
            print("Result: DISTINCT (No Match)")

    # Reset stdout
    sys.stdout = sys.__stdout__
    print(f"Test finished. Score: {score}")

    # Test Number Normalization logic explicitly
    print("-" * 50)
    print("Testing Number Normalization '千万':")
    # Access the inner function via a temporary instance or just copy-paste logic?
    # extract_key_features calls normalize_number internally.
    # We can inspect feat1['numbers'] to see if it parsed.
    
if __name__ == "__main__":
    test_similarity()
