import sys
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

# Add project root to path
# Add project root and crawler to path
sys.path.append(str(Path(__file__).parent / 'crawler'))
sys.path.append(str(Path(__file__).parent))

from database.db_sqlite import Database


def check_db():
    print("Initialize DB...")
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    # Check total counts
    cursor.execute("SELECT count(*), stage FROM news GROUP BY stage")
    rows = cursor.fetchall()
    print("--- News Counts by Stage ---")
    for r in rows:
        print(f"Stage: {r[1]}, Count: {r[0]}")
        
    # Check Date Range
    cursor.execute("SELECT min(published_at), max(published_at) FROM news")
    row = cursor.fetchone()
    print("\n--- Date Range in DB ---")
    print(f"Min: {row[0]}")
    print(f"Max: {row[1]}")
    
    # Check Last 24h Query
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    
    start_str = yesterday.isoformat()
    end_str = now.isoformat()
    
    print(f"\n--- Checking Query for Last 24h ({start_str} to {end_str}) ---")
    res = db.get_news_for_export(start_date=start_str, end_date=end_str, stage='raw')
    print(f"Items found (Stage=raw): {len(res)}")
    
    res = db.get_news_for_export(start_date=start_str, end_date=end_str, stage='deduplicated')
    print(f"Items found (Stage=deduplicated): {len(res)}")
    
    # Check All Time
    print("\n--- Checking Query All Time ---")
    res = db.get_news_for_export(stage='raw')
    print(f"Items found (Stage=raw): {len(res)}")

if __name__ == "__main__":
    check_db()
