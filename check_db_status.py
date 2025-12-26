import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'crawler'))
from database.db_sqlite import Database

try:
    db = Database()
    
    # 1. Check Blacklist
    keywords = db.get_blacklist_keywords()
    print(f"Total Blacklist Keywords: {len(keywords)}")
    for k in keywords[:5]:
        print(f" - {k['keyword']} ({k['match_type']})")

    # 2. Check Deduplicated News (Pending Filter)
    # Using raw SQL to be sure
    conn = db.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM deduplicated_news WHERE stage='deduplicated'")
    pending_count = cursor.fetchone()[0]
    
    print(f"Deduplicated News (Pending Filter): {pending_count}")
    
    # 3. Check Raw News
    cursor.execute("SELECT COUNT(*) FROM news WHERE stage='raw'")
    raw_count = cursor.fetchone()[0]
    print(f"Raw News (Wait for Deduplicate): {raw_count}")
    

    cursor.execute("SELECT count(*) FROM curated_news")
    curated_count = cursor.fetchone()[0]
    print(f"Curated News Count: {curated_count}")

    cursor.execute("SELECT id, title FROM curated_news LIMIT 5")
    print("Sample Curated News:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    cursor.execute("SELECT count(*) FROM keyword_blacklist")
    blacklist_count = cursor.fetchone()[0]
    print(f"Blacklist Keywords Count: {blacklist_count}")

    cursor.execute("SELECT keyword, match_type FROM keyword_blacklist")
    print("Blacklist Keywords:")
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]})")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
