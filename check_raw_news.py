import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
from database.db_sqlite import Database

db = Database()
conn = db.connect()
cursor = conn.cursor()

news_id = 221
print(f"Checking news table for id: {news_id}")

cursor.execute("SELECT * FROM news WHERE id = ?", (news_id,))
row = cursor.fetchone()

if row:
    print(dict(row))
else:
    print("News item not found in news table.")

conn.close()
