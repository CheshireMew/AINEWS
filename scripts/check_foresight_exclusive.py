import sqlite3
import os

db_path = 'ainews.db'

def check_exclusive():
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查用户日志中提到的几个URL
    urls = [
        'https://foresightnews.pro/article/detail/93570',
        'https://foresightnews.pro/article/detail/93536',
        'https://foresightnews.pro/article/detail/93527'
    ]
    
    print("检查这些URL在数据库中的状态:")
    for url in urls:
        cursor.execute('''
            SELECT id, title, source_site, author, published_at, scraped_at 
            FROM news 
            WHERE source_url = ?
        ''', (url,))
        row = cursor.fetchone()
        if row:
            print(f"\nURL: {url}")
            print(f"  ID: {row[0]}")
            print(f"  Title: {row[1][:50]}...")
            print(f"  Source Site: '{row[2]}'")
            print(f"  Author: '{row[3]}'")
            print(f"  Published: {row[4]}")
            print(f"  Scraped: {row[5]}")
        else:
            print(f"\n❌ URL不存在: {url}")
    
    # 检查 ForesightNews 独家 的最新5条记录
    print("\n\n=== ForesightNews 独家 最新5条记录 (按 published_at DESC) ===")
    cursor.execute('''
        SELECT source_url, title, published_at, scraped_at 
        FROM news 
        WHERE source_site = 'ForesightNews 独家' 
        ORDER BY published_at DESC 
        LIMIT 5
    ''')
    rows = cursor.fetchall()
    for row in rows:
        print(f"[{row[2]}] {row[1][:40]}...")
        print(f"  URL: {row[0]}")
        print(f"  Scraped: {row[3]}")
        print()
        
    conn.close()

if __name__ == "__main__":
    check_exclusive()
