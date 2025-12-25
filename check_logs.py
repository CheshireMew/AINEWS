import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
from database.db_sqlite import Database

db = Database()
conn = db.connect()
cursor = conn.cursor()

news_id = 221
print(f"Checking logs for news_id: {news_id}")

cursor.execute("SELECT * FROM processing_logs WHERE news_id = ?", (news_id,))
rows = cursor.fetchall()

if rows:
    for r in rows:
        print(dict(r))
else:
    print("No logs found for this news_id.")
    
# Also check by details match just in case
cursor.execute("SELECT * FROM processing_logs WHERE details LIKE '%Binance%'")
rows = cursor.fetchall()
print(f"\n--- Logs with 'Binance' in details ({len(rows)}) ---")
for r in rows[:5]:
    print(dict(r))

conn.close()
