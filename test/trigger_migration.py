
import sys
import os

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from crawler.database.db_sqlite import Database

def trigger_migration():
    print("Triggering database migration...")
    try:
        db = Database()
        conn = db.connect()
        print("Database connection successful -> Migration code in __init__ should have run.")
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    trigger_migration()
