import sqlite3
import sys
import os

db_path = 'ainews.db'

def check_news(news_ids):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"Checking IDs: {news_ids}")
    
    placeholders = ','.join('?' for _ in news_ids)
    try:
        cursor.execute(f"SELECT id, title, source_site, stage, duplicate_of FROM news WHERE id IN ({placeholders})", news_ids)
        rows = cursor.fetchall()
        for row in rows:
            print(f"\nID: {row['id']}")
            print(f"Title: {row['title']}")
            print(f"Stage: {row['stage']}")
            print(f"Duplicate Of: {row['duplicate_of']}")
    except Exception as e:
        print(f"Error: {e}")
        
    conn.close()

if __name__ == "__main__":
    # IDs from user screenshot
    check_news([1395, 1396])
