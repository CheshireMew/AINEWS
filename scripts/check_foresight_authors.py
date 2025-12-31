import sqlite3
import os

db_path = 'ainews.db'

def check_foresight_authors():
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check author distribution for legacy source_site
    print("Checking authors for 'ForesightNews Article'...")
    cursor.execute('''
        SELECT author, COUNT(*) 
        FROM news 
        WHERE source_site = 'ForesightNews Article'
        GROUP BY author
    ''')
    rows = cursor.fetchall()
    
    if rows:
        print(f"Found {len(rows)} author groups:")
        for row in rows:
            print(f"  - Author: '{row[0]}' | Count: {row[1]}")
    else:
        print("No records found for 'ForesightNews Article'.")
        
    conn.close()

if __name__ == "__main__":
    check_foresight_authors()
