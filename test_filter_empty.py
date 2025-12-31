from crawler.database.db_sqlite import Database
import sqlite3

def test_filter():
    db = Database()
    
    # Check if we have deduplicated articles
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM deduplicated_news WHERE type='article' AND stage='deduplicated'")
    count = cursor.fetchone()[0]
    print(f"Pending deduplicated articles: {count}")
    
    # Check blacklist
    cursor.execute("SELECT count(*) FROM keyword_blacklist WHERE type='article'")
    bl_count = cursor.fetchone()[0]
    print(f"Blacklist count: {bl_count}")
    conn.close()
    
    # Run filter
    print("Running filter_news_by_blacklist(time_range_hours=0, type_filter='article')...")
    result = db.filter_news_by_blacklist(time_range_hours=0, type_filter='article')
    print("Result:", result)

if __name__ == "__main__":
    test_filter()
