import sys
import os
import sqlite3
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.getcwd())
try:
    from crawler.filters.local_deduplicator import LocalDeduplicator
except ImportError:
    sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
    from filters.local_deduplicator import LocalDeduplicator

def check_consistency(news_id, f):
    log(f"\n--- Checking Consistency for ID {news_id} ---", f)
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    # Check 'news' table
    cursor.execute("SELECT id, title, stage, duplicate_of FROM news WHERE id = ?", (news_id,))
    row = cursor.fetchone()
    if row:
        log(f"[news table] ID: {row[0]}, Stage: {row[2]}, DupOf: {row[3]}", f)
    else:
        log(f"[news table] ID {news_id} NOT FOUND", f)
        
    # Check 'deduplicated_news' table
    cursor.execute("SELECT original_news_id, title FROM deduplicated_news WHERE original_news_id = ?", (news_id,))
    row = cursor.fetchone()
    if row:
        log(f"[deduplicated_news table] Found entry for Original ID: {row[0]}", f)
    else:
        log(f"[deduplicated_news table] NOT FOUND for Original ID: {news_id}", f)
        
    conn.close()

def log(msg, f):
    print(msg)
    f.write(msg + "\n")

def test_boost(t1, t2, f):
    log(f"\n--- Test Entity Boost for: ---", f)
    log(f"T1: {t1}", f)
    log(f"T2: {t2}", f)
    
    dedup = LocalDeduplicator()
    base_score = dedup.calculate_similarity(t1, t2)
    log(f"Base Score: {base_score}", f)
    
    ent1 = dedup.extract_entities(t1)
    ent2 = dedup.extract_entities(t2)
    log(f"Entities 1: {ent1}", f)
    log(f"Entities 2: {ent2}", f)
    
    # Simulate Boost
    if ent1 and ent2 and ent1 == ent2:
        boosted_score = base_score + 0.15
        log(f"Boosted Score (+0.15 for exact entity match): {boosted_score}", f)
        if boosted_score >= 0.5:
            log("✅ Would be deduped with boost", f)
        else:
            log("❌ Still not deduped", f)

if __name__ == "__main__":
    with open("consistency_test.log", "w", encoding="utf-8") as f:
        # Check why 1300 is 'raw'
        check_consistency(1300, f)
        
        # Test boost for Coinbase case
        t3 = "Coinbase：2026年加密市场将由永续合约、预测市场与稳定币支付主导"
        t4 = "Coinbase报告：加密市场正转向结构性驱动，三个领域将主导加密市场"
        test_boost(t3, t4, f)
