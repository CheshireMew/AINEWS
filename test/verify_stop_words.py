import sys
import os
import sqlite3
import io
from datetime import datetime, timedelta

# Force stdout to utf-8 to handle Chinese characters on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.getcwd())
try:
    from crawler.filters.local_deduplicator import LocalDeduplicator
except ImportError:
    sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
    from filters.local_deduplicator import LocalDeduplicator

def verify_stop_words():
    # Simulate "All Time" - e.g., last 30 days or all data
    hours = 24 * 30 * 6 # 6 months
    print(f"🚀 Loading news from last {hours} hours to verify Stop Words...")
    
    db_path = 'ainews.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    
    # Get all news to ensure high frequency words are detected
    cursor.execute("""
        SELECT id, title, content, source_url, source_site, published_at, scraped_at
        FROM news 
        WHERE published_at >= ?
        ORDER BY published_at DESC
        LIMIT 5000 
    """, (cutoff_time,))
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} items. Analyzing frequency...")
    
    news_list = [dict(row) for row in rows]
    
    if not news_list:
        print("No data found.")
        return

    deduplicator = LocalDeduplicator()
    # identify_duplicates will trigger the stop word print
    deduplicator.find_duplicates(news_list)

if __name__ == "__main__":
    verify_stop_words()
