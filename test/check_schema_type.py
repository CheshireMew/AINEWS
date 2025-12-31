
import sqlite3
import os

def check_schema():
    if not os.path.exists('ainews.db'):
        print("ainews.db not found")
        return

    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    tables = ['news', 'deduplicated_news', 'curated_news']
    for table in tables:
        print(f"Checking table: {table}")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            if 'type' in col_names:
                print(f"✅ 'type' column exists in {table}")
            else:
                print(f"❌ 'type' column MISSING in {table}")
                print(f"Columns: {col_names}")
        except Exception as e:
            print(f"Error checking {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_schema()
