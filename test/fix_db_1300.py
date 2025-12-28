import sqlite3
import os

db_path = 'ainews.db'
if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("UPDATE news SET stage = 'deduplicated' WHERE id = 1300 AND stage = 'raw'")
    if cursor.rowcount > 0:
        print(f"Successfully updated {cursor.rowcount} row(s) for ID 1300.")
        conn.commit()
    else:
        print("No rows updated. ID 1300 might not be in 'raw' stage or doesn't exist.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
