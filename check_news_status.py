import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
from database.db_sqlite import Database

db = Database()
conn = db.connect()
cursor = conn.cursor()

# title fragment
title_frag = "Binance 上线吉尔吉斯索姆稳定币"
print(f"Searching for title containing: {title_frag}")

# Check deduplicated_news first (where filtered items live)
cursor.execute("SELECT * FROM deduplicated_news WHERE title LIKE ?", (f'%{title_frag}%',))
rows = cursor.fetchall()

if rows:
    print("\n--- Found in deduplicated_news ---")
    for r in rows:
        print(dict(r))
else:
    # Check raw news
    cursor.execute("SELECT * FROM news WHERE title LIKE ?", (f'%{title_frag}%',))
    rows = cursor.fetchall()
    if rows:
        print("\n--- Found in raw news ---")
        for r in rows:
            print(dict(r))
    else:
        print("News item NOT FOUND in DB.")

conn.close()
