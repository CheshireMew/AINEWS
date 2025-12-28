import sys
import os

sys.path.insert(0, os.getcwd())
try:
    from crawler.filters.local_deduplicator import LocalDeduplicator
except ImportError:
    sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
    from filters.local_deduplicator import LocalDeduplicator

def test_year_bias():
    dedup = LocalDeduplicator()
    
    # Case: Different topics, shared year "2026"
    t1 = "Bitcoin recovery in 2026"
    t2 = "Real Estate market forecast 2026"
    
    print(f"--- Comparison: '{t1}' vs '{t2}' ---")
    
    feat1 = dedup.extract_key_features(t1)
    feat2 = dedup.extract_key_features(t2)
    
    print(f"Numbers 1: {feat1['numbers']}")
    print(f"Numbers 2: {feat2['numbers']}")
    
    # Calculate score
    score = dedup.calculate_similarity(t1, t2)
    print(f"Similarity Score: {score}")
    
    # Check if number bonus was applied
    # We can infer it if score is significantly higher than keyword overlap would suggest
    if score >= 0.3:
        print("⚠️  High score detected! Likely due to Year Number Bonus.")
    else:
        print("✅ Low score. Year processed correctly.")

if __name__ == "__main__":
    test_year_bias()
