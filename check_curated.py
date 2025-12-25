import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
from database.db_sqlite import Database
db = Database()
conn = db.connect()
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM curated_news")
print(f"Curated Count: {cursor.fetchone()[0]}")
cursor.execute("SELECT count(*) FROM deduplicated_news WHERE stage='filtered'")
print(f"Filtered Count: {cursor.fetchone()[0]}")
conn.close()
