import sqlite3
import os

DB_PATH = 'ainews.db'

def inspect_db():
    if not os.path.exists(DB_PATH):
        print("Database not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n--- deduplicated_news types ---")
    try:
        cursor.execute("SELECT type, count(*) FROM deduplicated_news GROUP BY type")
        rows = cursor.fetchall()
        for row in rows:
            print(f"Type: {row[0]}, Count: {row[1]}")
    except Exception as e:
        print(f"Error querying deduplicated_news: {e}")

    print("\n--- deduplicated_news sample items ---")
    try:
        cursor.execute("SELECT id, title, type, stage FROM deduplicated_news LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print(e)
        
    conn.close()

if __name__ == "__main__":
    inspect_db()
