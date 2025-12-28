import sqlite3

def check_schema():
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(news)")
    columns = cursor.fetchall()
    print("Columns in 'news' table:")
    found = False
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
        if col[1] == 'duplicate_reason':
            found = True
    
    if found:
        print("✅ duplicate_reason column EXISTS.")
    else:
        print("❌ duplicate_reason column MISSING.")
    conn.close()

if __name__ == "__main__":
    check_schema()
