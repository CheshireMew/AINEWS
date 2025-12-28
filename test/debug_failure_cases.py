import sys
import os
import sqlite3
import warnings
import io

# Force stdout to utf-8 just in case, but we will write to file mostly
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.getcwd())
try:
    from crawler.filters.local_deduplicator import LocalDeduplicator
except ImportError:
    sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
    from filters.local_deduplicator import LocalDeduplicator

def log(msg, f):
    print(msg)
    f.write(msg + "\n")

def check_db_status(ids, f):
    log(f"\n--- Database Status for IDs: {ids} ---", f)
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in ids)
    cursor.execute(f"SELECT id, title, stage, duplicate_of, published_at, scraped_at FROM news WHERE id IN ({placeholders})", ids)
    rows = cursor.fetchall()
    for row in rows:
        log(f"ID: {row[0]}, Stage: {row[2]}, DupOf: {row[3]}", f)
        log(f"  Pub: {row[4]}", f)
        log(f"  Title: {row[1]}", f)
    conn.close()

def debug_pair(id1, title1, id2, title2, f):
    log(f"\n--- Debug Pair: {id1} vs {id2} ---", f)
    log(f"Title 1: {title1}", f)
    log(f"Title 2: {title2}", f)
    
    dedup = LocalDeduplicator()
    
    # 1. Similarity
    score = dedup.calculate_similarity(title1, title2)
    log(f"Similarity Score: {score}", f)
    
    # 2. Key Features
    feat1 = dedup.extract_key_features(title1)
    feat2 = dedup.extract_key_features(title2)
    log(f"Normalized 1: {feat1['normalized']}", f)
    log(f"Normalized 2: {feat2['normalized']}", f)
    
    # 3. Entities
    ent1 = dedup.extract_entities(title1)
    ent2 = dedup.extract_entities(title2)
    log(f"Entities 1: {ent1}", f)
    log(f"Entities 2: {ent2}", f)
    
    if ent1 and ent2 and not (ent1 & ent2):
        log("❌ Entity Mismatch! Force 0.0", f)
    else:
        log("✅ Entity Check Passed (Intersection or empty)", f)

if __name__ == "__main__":
    with open("test_result.log", "w", encoding="utf-8") as f:
        # Case 1: Identical
        t1 = "分析师：比特币无需等待黄金和白银回调，仍可延续其上行走势"
        t2 = "分析师：比特币无需等待黄金和白银回调，仍可延续其上行走势"
        # Database check
        check_db_status([1298, 1300], f)
        debug_pair(1298, t1, 1300, t2, f)
        
        # Case 2: Similar
        t3 = "Coinbase：2026年加密市场将由永续合约、预测市场与稳定币支付主导"
        t4 = "Coinbase报告：加密市场正转向结构性驱动，三个领域将主导加密市场"
        check_db_status([1288, 1283], f)
        debug_pair(1288, t3, 1283, t4, f)
