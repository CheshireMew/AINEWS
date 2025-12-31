
import sqlite3
import os

def fix_schema():
    if not os.path.exists('ainews.db'):
        print("ainews.db not found")
        return

    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    columns_to_add = [
        ('curated_news', 'ai_status', 'TEXT'),
        ('curated_news', 'ai_summary', 'TEXT'),
        ('curated_news', 'ai_explanation', 'TEXT'),
        ('curated_news', 'ai_score', 'INTEGER'),
        ('curated_news', 'ai_category', 'TEXT'),
        ('curated_news', 'push_status', "TEXT DEFAULT 'pending'"),
        ('curated_news', 'pushed_at', 'TIMESTAMP')
    ]
    
    for table, col, defn in columns_to_add:
        try:
            print(f"Adding {col} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
            print(f"✅ Added {col}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"ℹ️ {col} already exists")
            else:
                print(f"❌ Failed to add {col}: {e}")
                
    conn.commit()
    conn.close()
    print("Schema fix complete.")

if __name__ == "__main__":
    fix_schema()
