import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    # 查询最近被过滤的新闻及其过滤原因
    cursor.execute("""
        SELECT id, title, keyword_filter_reason, stage
        FROM deduplicated_news
        WHERE stage = 'filtered'
        ORDER BY deduplicated_at DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    print("=== 最近过滤的新闻 ===")
    for row in rows:
        news_id, title, reason, stage = row
        print(f"\nID: {news_id}")
        print(f"标题: {title[:50]}...")
        print(f"过滤原因: {reason if reason else 'NULL/EMPTY'}")
        print(f"状态: {stage}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
