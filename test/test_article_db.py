
import sys
import os

# Add crawler directory to path (matching backend/main.py logic)
# .. from test is root. crawler is at root/crawler.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
crawler_path = os.path.join(project_root, 'crawler')

if crawler_path not in sys.path:
    sys.path.insert(0, crawler_path)

print(f"Crawler path added: {crawler_path}")

try:
    from database.db_sqlite import Database
    print("Import successful: from database.db_sqlite import Database")
except ImportError as e:
    print(f"Import failed: {e}")
    raise e

from datetime import datetime
import time

def test_article_filtering():
    db = Database('ainews.db')
    conn = db.connect()
    cursor = conn.cursor()
    
    # 1. Insert a test Article
    article_id = 9999991
    cursor.execute("""
        INSERT INTO news (id, title, content, published_at, source_site, source_url, type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (article_id, "Test Article Item", "Content of article", datetime.now(), "Test", "http://test.com/article", "article"))
    
    # 2. Insert a test News
    news_id = 9999992
    cursor.execute("""
        INSERT INTO news (id, title, content, published_at, source_site, source_url, type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (news_id, "Test News Item", "Content of news", datetime.now(), "Test", "http://test.com/news", "news"))
    
    conn.commit()
    conn.close()
    
    try:
        # 3. Test Retrieve 'article'
        print("Testing get_news_by_time_range(type_filter='article')...")
        articles = db.get_news_by_time_range(hours=24, type_filter='article')
        found_article = any(item['id'] == article_id for item in articles)
        found_news_in_articles = any(item['id'] == news_id for item in articles)
        
        if found_article and not found_news_in_articles:
            print("✅ Successfully retrieved ID 9999991 (Article) and excluded News.")
        else:
            print(f"❌ Failed. Found Article: {found_article}, Found News in Articles: {found_news_in_articles}")
            
        # 4. Test Retrieve 'news'
        print("Testing get_news_by_time_range(type_filter='news')...")
        news_items = db.get_news_by_time_range(hours=24, type_filter='news')
        found_news = any(item['id'] == news_id for item in news_items)
        found_article_in_news = any(item['id'] == article_id for item in news_items)
        
        if found_news and not found_article_in_news:
             print("✅ Successfully retrieved ID 9999992 (News) and excluded Article.")
        else:
             print(f"❌ Failed. Found News: {found_news}, Found Article in News: {found_article_in_news}")
             
    finally:
        # Cleanup
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM news WHERE id IN (?, ?)", (article_id, news_id))
        conn.commit()
        conn.close()
        print("Test data cleaned up.")

if __name__ == "__main__":
    test_article_filtering()
