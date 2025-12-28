
import sqlite3
import os

def inspect_db():
    db_path = 'ainews.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Find the "Gold" news
    print("--- Searching for Gold News ---")
    cursor.execute("SELECT id, title, duplicate_of FROM news WHERE title LIKE '%现货黄金今晨涨破%'")
    gold_news = cursor.fetchall()
    
    gold_id = None
    if gold_news:
        for row in gold_news:
            print(f"Found Gold News: ID={row[0]}, Title={row[1]}, DuplicateOf={row[2]}")
            gold_id = row[0]
    else:
        print("Gold news not found.")

    if gold_id:
        # 2. Find items that are duplicates of this Gold news
        print(f"\n--- Checking duplicates of ID {gold_id} ---")
        cursor.execute("SELECT count(*) FROM news WHERE duplicate_of = ?", (gold_id,))
        count = cursor.fetchone()[0]
        print(f"Count of items duplicated of {gold_id}: {count}")

        cursor.execute("SELECT id, title FROM news WHERE duplicate_of = ? LIMIT 5", (gold_id,))
        rows = cursor.fetchall()
        for row in rows:
            print(f"  - [{row[0]}] {row[1]}")

    # 3. Check the "SlowMist" news specific case
    print("\n--- Checking SlowMist News ---")
    cursor.execute("SELECT id, title, duplicate_of FROM news WHERE title LIKE '%慢雾余弦%'")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  - ID={row[0]}, Title={row[1]}, DuplicateOf={row[2]}")
        if row[2] and gold_id and row[2] == gold_id:
            print("    -> CONFIRMED: Linked to Gold News")

    conn.close()

if __name__ == "__main__":
    inspect_db()
