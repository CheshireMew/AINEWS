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

def log(msg, f):
    print(msg)
    f.write(msg + "\n")

def check_db(ids, f):
    log(f"\n--- Database Status for IDs {ids} ---", f)
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in ids)
    cursor.execute(f"SELECT id, title, stage, duplicate_of, published_at FROM news WHERE id IN ({placeholders})", ids)
    rows = cursor.fetchall()
    for row in rows:
        log(f"ID: {row[0]}, Stage: {row[2]}, DupOf: {row[3]}", f)
        log(f"  Pub: {row[4]}", f)
        title_snippet = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
        log(f"  Title: {title_snippet}", f)
    conn.close()

def debug_pair(id1, t1, id2, t2, f):
    log(f"\n--- Comparison: {id1} vs {id2} ---", f)
    log(f"T1: {t1}", f)
    log(f"T2: {t2}", f)
    
    dedup = LocalDeduplicator()
    
    score = dedup.calculate_similarity(t1, t2)
    log(f"Similarity Score: {score}", f)
    
    if score >= dedup.similarity_threshold:
        log("✅ Result: DUPLICATE (Algorithm would link them)", f)
    else:
        log("❌ Result: INDEPENDENT (Algorithm would NOT link them)", f)

if __name__ == "__main__":
    with open("check_status.log", "w", encoding="utf-8") as f:
        # Group 1: Lighter (1279, 1280)
        check_db([1279, 1280], f)
        
        # Group 2: Coinbase Premium (1276, 1275)
        check_db([1276, 1275], f)
        
        # Check Similarity for Coinbase pair
        conn = sqlite3.connect('ainews.db')
        cursor = conn.cursor()
        t1276 = cursor.execute("SELECT title FROM news WHERE id=1276").fetchone()
        t1275 = cursor.execute("SELECT title FROM news WHERE id=1275").fetchone()
        conn.close()
        
        if t1276 and t1275:
            debug_pair(1276, t1276[0], 1275, t1275[0], f)
        else:
            log("Could not find titles for 1276/1275", f)
