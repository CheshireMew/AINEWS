
import sqlite3
import os

# Confirmed correct DB
DB_PATH = r'e:\Work\Code\AINEWS\AINews\ainews.db'

def export_titles():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    print(f"Connecting to {DB_PATH}...")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        titles = set()
        
        # User requested "deduplicated database"
        # Interpreted as ONLY unique news that passed deduplication (deduplicated_news table)
        # OR news with stage='deduplicated' in news table?
        # Let's export both UNIQUE titles (no duplicates)
        
        # 1. Query deduplicated_news table
        print("Querying deduplicated_news table...")
        try:
            cursor.execute("SELECT title FROM deduplicated_news")
            rows = cursor.fetchall()
            for row in rows:
                if row[0]: titles.add(row[0].strip())
            print(f"  Found {len(rows)} titles.")
        except Exception as e:
            print(f"  Error: {e}")

        # 2. Query news table where stage='deduplicated'
        # The user specifically said "deduplicated database"
        # They might imply they don't want "raw" news.
        print("Querying news table (stage='deduplicated')...")
        try:
            cursor.execute("SELECT title FROM news WHERE stage = 'deduplicated'")
            rows = cursor.fetchall()
            for row in rows:
                if row[0]: titles.add(row[0].strip())
            print(f"  Found {len(rows)} titles.")
        except Exception as e:
            print(f"  Error: {e}")
            
        # Write to file
        sorted_titles = sorted(list(titles))
        with open('titles.txt', 'w', encoding='utf-8') as f:
            for t in sorted_titles:
                f.write(t + '\n')
        
        print(f"Successfully exported {len(sorted_titles)} UNIQUE deduplicated titles to {os.path.abspath('titles.txt')}")
        conn.close()
        
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    export_titles()
