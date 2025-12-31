
import sqlite3
import os

def check_schema_ai_score():
    if not os.path.exists('ainews.db'):
        print("ainews.db not found")
        return

    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    table = 'curated_news'
    print(f"Checking table: {table}")
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_names = [col[1] for col in columns]
        
        missing = []
        for col in ['ai_score', 'ai_category']:
            if col in col_names:
                print(f"✅ '{col}' column exists in {table}")
            else:
                print(f"❌ '{col}' column MISSING in {table}")
                missing.append(col)
        
        if missing:
            print(f"Missing columns: {missing}")
        else:
            print("All verified columns exist.")
            
    except Exception as e:
        print(f"Error checking {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_schema_ai_score()
