import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

cutoff = (datetime.now() - timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')

cursor.execute("SELECT stage, COUNT(*) FROM deduplicated_news WHERE deduplicated_at >= ? GROUP BY stage", (cutoff,))
print("Dedup Table Stages:")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]}")

cursor.execute("SELECT COUNT(*) FROM deduplicated_news WHERE deduplicated_at >= ? AND stage = 'deduplicated'", (cutoff,))
print(f"\nPending for filter: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM curated_news WHERE curated_at >= ?", (cutoff,))
print(f"Curated total: {cursor.fetchone()[0]}")

conn.close()
