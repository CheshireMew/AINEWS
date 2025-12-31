import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# 简单的模拟 get_beijing_time，避免复杂导入
from datetime import datetime
def get_beijing_time(): return datetime.now()

def check_recent_news():
    conn = sqlite3.connect('crawler/data/news.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n=== 最近抓取的原始新闻 ===")
    cursor.execute("SELECT id, title, type, scraped_at, stage FROM news ORDER BY scraped_at DESC LIMIT 10")
    for row in cursor.fetchall():
        print(f"ID: {row['id']}, Type: {row['type']}, Stage: {row['stage']}, Time: {row['scraped_at']}, Title: {row['title'][:30]}...")

    print("\n=== 最近去重后的新闻 ===")
    cursor.execute("SELECT id, title, type, stage, deduplicated_at FROM deduplicated_news ORDER BY deduplicated_at DESC LIMIT 10")
    for row in cursor.fetchall():
        print(f"ID: {row['id']}, Type: {row['type']}, Stage: {row['stage']}, Time: {row['deduplicated_at']}, Title: {row['title'][:30]}...")
        
    print("\n=== 最近精选的新闻 ===")
    cursor.execute("SELECT id, title, type, stage, curated_at FROM curated_news ORDER BY curated_at DESC LIMIT 10")
    for row in cursor.fetchall():
        print(f"ID: {row['id']}, Type: {row['type']}, Stage: {row['stage']}, Time: {row['curated_at']}, Title: {row['title'][:30]}...")

    conn.close()

if __name__ == "__main__":
    check_recent_news()
