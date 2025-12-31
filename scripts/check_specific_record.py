import sqlite3
import os

db_path = 'ainews.db'

def check_specific():
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 93356 is LazAI
    url_part = '93356'
    print(f"Checking records with URL containing {url_part}...")
    
    cursor.execute("SELECT id, title, author, source_site, scraped_at FROM news WHERE source_url LIKE ?", (f'%{url_part}%',))
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID: {row[0]}")
        print(f"Title: {row[1]}")
        print(f"Author: '{row[2]}'")
        print(f"Source Site: '{row[3]}'")
        print(f"Scraped At: {row[4]}")
        print("-" * 20)
        
    conn.close()

if __name__ == "__main__":
    check_specific()
