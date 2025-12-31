import sqlite3
import os

def check_sequence():
    db_path = 'ainews.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("--- SQLite Sequence ---")
        cursor.execute("SELECT * FROM sqlite_sequence WHERE name='news'")
        seq = cursor.fetchone()
        print(f"Sequence for 'news': {seq}")
        
        print("\n--- Max ID in 'news' table ---")
        cursor.execute("SELECT MAX(id), MIN(id), COUNT(*) FROM news")
        stats = cursor.fetchone()
        print(f"Max ID: {stats[0]}")
        print(f"Min ID: {stats[1]}")
        print(f"Total Count: {stats[2]}")
        
        print("\n--- Top 10 Highest IDs ---")
        cursor.execute("SELECT id, title, created_at FROM news ORDER BY id DESC LIMIT 10")
        for row in cursor.fetchall():
            print(row)
            
        print("\n--- ID Gap Analysis (Checking for jumps > 1000) ---")
        # Check for large gaps which indicate skips
        cursor.execute("SELECT id FROM news ORDER BY id")
        ids = [r[0] for r in cursor.fetchall()]
        if ids:
            prev = ids[0]
            jumps = []
            for curr in ids[1:]:
                if curr - prev > 1000:
                    jumps.append((prev, curr))
                prev = curr
            
            if jumps:
                print(f"Found {len(jumps)} large jumps (>1000):")
                for j in jumps[:5]:
                    print(f"Jump from {j[0]} to {j[1]} (Gap: {j[1]-j[0]})")
            else:
                print("No large gaps (>1000) found.")
                
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_sequence()
