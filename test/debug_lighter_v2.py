import sys
import os
import sqlite3
import io

# Force stdout to utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.getcwd())
try:
    from crawler.filters.local_deduplicator import LocalDeduplicator
except ImportError:
    sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
    from filters.local_deduplicator import LocalDeduplicator

def log(msg):
    print(msg)

def check_db(ids):
    log(f"--- Checking DB for IDs {ids} ---")
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in ids)
    cursor.execute(f"SELECT id, title, stage, duplicate_of FROM news WHERE id IN ({placeholders})", ids)
    rows = cursor.fetchall()
    for row in rows:
        log(f"ID: {row[0]}, Stage: {row[2]}, DupOf: {row[3]}")
    conn.close()

def debug_dedup():
    t1 = "Lighter创始人：不会公开反女巫算法，我们对筛查结果有信心"
    t2 = "Lighter 创始人：不会公开反女巫算法，若遭误判可申诉"
    
    dedup = LocalDeduplicator()
    
    # Check Entities
    e1 = dedup.extract_entities(t1)
    e2 = dedup.extract_entities(t2)
    log(f"Entities 1 ('{t1[:10]}...'): {e1}")
    log(f"Entities 2 ('{t2[:10]}...'): {e2}")
    
    # Check Similarity
    score = dedup.calculate_similarity(t1, t2)
    log(f"Similarity Score: {score}")
    
    if score >= dedup.similarity_threshold:
        log("✅ Result: DUPLICATE")
    else:
        log("❌ Result: INDEPENDENT (Still failing?)")

if __name__ == "__main__":
    check_db([1279, 1280])
    debug_dedup()
