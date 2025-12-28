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

def log(msg, f=None):
    if f:
        f.write(msg + "\n")
    print(msg)

def check_pair(id1, id2):
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT id, title, stage, duplicate_of, published_at FROM news WHERE id IN ({id1}, {id2})")
    rows = cursor.fetchall()
    
    t1 = ""
    t2 = ""
    
    with open("debug_1271.log", "w", encoding="utf-8") as f:
        log("--- DB Status ---", f)
        for row in rows:
            log(f"ID: {row[0]}, Stage: {row[2]}, DupOf: {row[3]}, Pub: {row[4]}", f)
            log(f"Title: {row[1]}", f)
            if row[0] == id1: t1 = row[1]
            if row[0] == id2: t2 = row[1]
        
        conn.close()
        
        if t1 and t2:
            dedup = LocalDeduplicator()
            score = dedup.calculate_similarity(t1, t2)
            log(f"\n--- Similarity Check ---", f)
            log(f"Title 1: {t1}", f)
            log(f"Title 2: {t2}", f)
            log(f"Score: {score}", f)
            
            feat1 = dedup.extract_key_features(t1)
            feat2 = dedup.extract_key_features(t2)
            
            log(f"\nFeat 1 Keywords: {feat1['keywords']}", f)
            log(f"Feat 2 Keywords: {feat2['keywords']}", f)
            log(f"Intersection: {feat1['keywords'] & feat2['keywords']}", f)
            
            ent1 = dedup.extract_entities(t1)
            ent2 = dedup.extract_entities(t2)
            log(f"Entities 1: {ent1}", f)
            log(f"Entities 2: {ent2}", f)

if __name__ == "__main__":
    check_pair(1271, 1288)
