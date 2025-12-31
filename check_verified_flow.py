import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    # 检查 deduplicated_news 中各状态的数量
    cursor.execute("SELECT stage, COUNT(*) FROM deduplicated_news GROUP BY stage")
    dedup_stats = cursor.fetchall()
    
    print("=== deduplicated_news 表状态统计 ===")
    for stage, count in dedup_stats:
        print(f"{stage}: {count} 条")
    
    # 检查 curated_news 总数
    cursor.execute("SELECT COUNT(*) FROM curated_news")
    curated_count = cursor.fetchone()[0]
    print(f"\n=== curated_news 表总数 ===")
    print(f"总计: {curated_count} 条")
    
    # 检查 verified 的新闻是否都在 curated_news 中
    cursor.execute("""
        SELECT COUNT(*) FROM deduplicated_news d
        WHERE d.stage = 'verified'
        AND NOT EXISTS (
            SELECT 1 FROM curated_news c 
            WHERE c.source_url = d.source_url
        )
    """)
    missing_count = cursor.fetchone()[0]
    
    if missing_count > 0:
        print(f"\n⚠️  发现问题：{missing_count} 条 verified 新闻未进入 curated_news")
        print("\n正在显示前 5 条缺失的新闻：")
        cursor.execute("""
            SELECT id, title, stage FROM deduplicated_news d
            WHERE d.stage = 'verified'
            AND NOT EXISTS (
                SELECT 1 FROM curated_news c 
                WHERE c.source_url = d.source_url
            )
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  ID: {row[0]}, Title: {row[1][:50]}...")
    else:
        print(f"\n✅ 所有 verified 新闻都已正确进入 curated_news")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
