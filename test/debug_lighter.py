import sys
import os
import re
sys.path.insert(0, os.getcwd())
from crawler.filters.local_deduplicator import LocalDeduplicator

def debug_dedup(id1, title1, id2, title2):
    print(f"Debug: {id1} vs {id2}")
    print(f"Title 1: {title1}")
    print(f"Title 2: {title2}")
    
    dedup = LocalDeduplicator()
    
    # 1. Check Similarity
    score = dedup.calculate_similarity(title1, title2)
    print(f"Similarity Score: {score}")
    
    # 2. Check Entity Extraction
    ent1 = dedup.extract_entities(title1)
    ent2 = dedup.extract_entities(title2)
    print(f"Entities 1: {ent1}")
    print(f"Entities 2: {ent2}")
    
    if ent1 and ent2 and not (ent1 & ent2):
        print("❌ Entity Mismatch! This would force similarity to 0.0")
    else:
        print("✅ Entity Check passed (intersection found or one empty)")

    # 3. Specific Regex Test
    print("\nRegex Debug:")
    cap_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    print(f"Pattern: {cap_pattern}")
    print(f"Match 1: {re.findall(cap_pattern, title1)}")
    print(f"Match 2: {re.findall(cap_pattern, title2)}")
    
    # Test word boundary behavior
    print(f"'Lighter' boundary check in '{title1}':", re.search(r'\bLighter\b', title1))

if __name__ == "__main__":
    t1 = "Lighter创始人：不会公开反女巫算法，我们对筛查结果有信心"
    t2 = "Lighter 创始人：不会公开反女巫算法，若遭误判可申诉"
    debug_dedup(1279, t1, 1280, t2)
