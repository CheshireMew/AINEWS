import sqlite3
import re
import os

DB_PATH = "ainews.db"

def clean_titles():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get BlockBeats news
    cursor.execute("SELECT id, title FROM news WHERE source_site = 'blockbeats'")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} BlockBeats items.")
    
    updated_count = 0
    pattern = re.compile(r"^\d{1,2}:\d{2}\s*")
    
    for row in rows:
        news_id, title = row
        new_title = pattern.sub("", title)
        
        if new_title != title:
            cursor.execute("UPDATE news SET title = ? WHERE id = ?", (new_title, news_id))
            updated_count += 1
            print(f"cleaned: {title} -> {new_title}")
            
    conn.commit()
    conn.close()
    print(f"Finished. Updated {updated_count} titles.")

if __name__ == "__main__":
    clean_titles()
