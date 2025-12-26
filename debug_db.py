import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())
# Add backend to path manually just in case
sys.path.append(os.path.join(os.getcwd(), 'backend'))

print("Sys Path:", sys.path)

try:
    from crawler.database.db_sqlite import Database
except ImportError as e:
    print(f"Import Error: {e}")
    # Try importing core directly to test
    try:
        import core.db_base
        print("Core imported successfully")
    except ImportError as e2:
        print(f"Core Import Error: {e2}")
    raise

def check_data():
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    print(f"Using DB: {db.db_path}")
    print(f"Server Time: {datetime.now()}")
    
    cutoff = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
    print(f"Cutoff Time (2h ago): {cutoff}")

    # Check count using the EXACT query from main.py
    query = "SELECT COUNT(*) FROM curated_news WHERE curated_at >= ? AND (ai_status IS NULL OR ai_status = '' OR ai_status = 'pending')"
    print(f"Query: {query}")
    print(f"Params: {(cutoff,)}")
    
    cursor.execute(query, (cutoff,))
    count = cursor.fetchone()[0]
    print(f"Count Result: {count}")
    
    # Dump some rows
    cursor.execute("SELECT id, curated_at, ai_status FROM curated_news WHERE curated_at >= ? LIMIT 5", (cutoff,))
    print("\nMatching Rows:")
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":
    check_data()
