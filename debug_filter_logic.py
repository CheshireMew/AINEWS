import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
from database.db_sqlite import Database
import datetime

db = Database()
print(f"DB Path: {db.db_path}")

try:
    conn = db.connect()
    cursor = conn.cursor()
    
    # 1. Check Keywords
    cursor.execute("SELECT count(*) FROM keyword_blacklist")
    print(f"Keywords Count: {cursor.fetchone()[0]}")
    
    # 2. Check Deduplicated Items and their Timestamps
    print("\n--- Deduplicated News Sample ---")
    cursor.execute("SELECT id, title, deduplicated_at, stage FROM deduplicated_news LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(dict(row))
        
    # 3. Simulate Filter Query
    time_range_hours = 24
    start_time = (datetime.datetime.now() - datetime.timedelta(hours=time_range_hours)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"\nScanning since: {start_time}")
    
    query = '''
        SELECT count(*)
        FROM deduplicated_news 
        WHERE deduplicated_at >= ? AND stage = 'deduplicated'
    '''
    cursor.execute(query, (start_time,))
    count = cursor.fetchone()[0]
    print(f"Items matching query: {count}")

    if count == 0:
        print("⚠️ No items matched! Checking if deduplicated_at format matches...")
        cursor.execute("SELECT deduplicated_at FROM deduplicated_news ORDER BY deduplicated_at DESC LIMIT 1")
        last_item = cursor.fetchone()
        if last_item:
            print(f"Latest Item Timestamp: {last_item[0]}")
            print(f"Is Latest ({last_item[0]}) >= Start ({start_time})? {last_item[0] >= start_time}")
            
    print("\n--- Running Actual Filter Method ---")
    result = db.filter_news_by_blacklist(time_range_hours=24)
    print("Filter Result:", result)
    
    conn.commit()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
