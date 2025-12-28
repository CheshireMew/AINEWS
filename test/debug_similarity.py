
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from crawler.filters.local_deduplicator import LocalDeduplicator

dedup = LocalDeduplicator()
t1 = "Bitcoin surges to 50k"
t2 = "Bitcoin hits 50,000 dollars"

print("-" * 50)
print(f"Title 1: {t1}")
print(f"Title 2: {t2}")

f1 = dedup.extract_key_features(t1)
f2 = dedup.extract_key_features(t2)

print("\nFeatures 1:")
print(f"  Norm: {f1['normalized']}")
print(f"  Nums: {f1['numbers']}")
print(f"  KWs:  {f1['keywords']}")

print("\nFeatures 2:")
print(f"  Norm: {f2['normalized']}")
print(f"  Nums: {f2['numbers']}")
print(f"  KWs:  {f2['keywords']}")

sim = dedup.calculate_similarity_from_features(f1, f2)
print(f"\nTotal Similarity: {sim}")
