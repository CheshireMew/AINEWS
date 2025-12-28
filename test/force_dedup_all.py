import sys
import os
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.getcwd())
try:
    from crawler.filters.local_deduplicator import LocalDeduplicator
except ImportError:
    sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
    from filters.local_deduplicator import LocalDeduplicator

def force_dedup(hours=24):
    print(f"🚀 Starting Force Deduplication (Last {hours} hours)...")
    
    db_path = 'ainews.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # query all news (raw + deduplicated) in range
    cutoff_time = (datetime.now() - timedelta(hours=hours)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"Cutoff Time: {cutoff_time}")
    
    cursor.execute("""
        SELECT id, title, content, source_url, source_site, published_at, scraped_at, duplicate_of
        FROM news 
        WHERE (stage = 'raw' OR stage = 'deduplicated' OR stage = 'pending' OR stage = 'duplicate') AND published_at >= ?
        ORDER BY published_at DESC
    """, (cutoff_time,))
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} items to process.")
    
    if not rows:
        return

    # Convert to list of dicts
    news_list = []
    for row in rows:
        news_list.append(dict(row))
        
    # Run Deduplicator
    deduplicator = LocalDeduplicator()
    marked_news = deduplicator.mark_duplicates(news_list)
    
    mark_count = 0
    dup_ids = []
    
    # Update DB
    for news in marked_news:
        raw_id = news['id']
        if news.get('is_local_duplicate', False):
            # 是重复项
            dup_of = news.get('duplicate_of')
            cursor.execute("""
                UPDATE news 
                SET stage = 'duplicate', duplicate_of = ? 
                WHERE id = ?
            """, (dup_of, raw_id))
            mark_count += 1
            dup_ids.append(raw_id)
        else:
            # 💡 FIX: 必须显式更新非重复项，清除旧的关联！
            # 否则之前错误的 duplicate_of 链接会残留
            cursor.execute("""
                UPDATE news 
                SET stage = 'deduplicated', duplicate_of = NULL
                WHERE id = ?
            """, (raw_id,))
            
    conn.commit()
    conn.close()
    print(f"✅ Completed. Marked {mark_count} duplicates.")
    print(f"Duplicate IDs: {dup_ids}")

if __name__ == "__main__":
    force_dedup(24) # Force last 24 hours
