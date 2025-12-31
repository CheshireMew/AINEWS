import sqlite3
import os

db_path = 'ainews.db'

def check_last():
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check for ForesightNews 深度
    print("\n=== ForesightNews 深度 ===")
    cursor.execute('''
        SELECT source_url, title, scraped_at 
        FROM news 
        WHERE source_site = 'ForesightNews 深度' 
        ORDER BY scraped_at DESC 
        LIMIT 5
    ''')
    rows = cursor.fetchall()
    for row in rows:
        print(f"[{row[2]}] {row[1]} ({row[0]})")
        
    conn.close()

if __name__ == "__main__":
    check_last()
