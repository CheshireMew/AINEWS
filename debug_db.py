import sqlite3
from pathlib import Path

db_path = str(Path(__file__).parent / 'ainews.db')
print(f"Checking DB at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Count by source
    cursor.execute("SELECT source_site, COUNT(*) as count FROM news GROUP BY source_site")
    rows = cursor.fetchall()
    print("\n--- Summary by Source ---")
    for row in rows:
        print(f"{row['source_site']}: {row['count']}")

    # Check recent odaily items
    print("\n--- Recent Odaily Items ---")
    cursor.execute("SELECT id, title, source_site, scraped_at FROM news WHERE source_site = 'odaily' ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    if not rows:
        print("No odaily items found.")
    else:
        for row in rows:
            print(f"ID: {row['id']}, Title: {row['title']}, Time: {row['scraped_at']}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
