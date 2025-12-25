import sqlite3
from pathlib import Path
import json

db_path = str(Path(__file__).parent / 'ainews.db')
print(f"Checking DB at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Check for Odaily items (limit 5)
    print("\n=== Recent Odaily Items ===")
    cursor.execute("SELECT id, title, published_at, scraped_at, content FROM news WHERE source_site = 'odaily' ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    if not rows:
        print("No odaily items found.")
    else:
        for row in rows:
            content_preview = row['content'][:50] + "..." if row['content'] else "EMPTY"
            print(f"ID: {row['id']}")
            print(f"Title: {row['title']}")
            print(f"Published: {row['published_at']}")
            print(f"Scraped: {row['scraped_at']}")
            print(f"Content: {content_preview}")
            print("-" * 20)

    # 2. Check for Blockbeats items (check title format)
    print("\n=== Recent Blockbeats Items ===")
    cursor.execute("SELECT id, title FROM news WHERE source_site LIKE '%blockbeats%' ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(f"ID: {row['id']} | Title: {row['title']}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
