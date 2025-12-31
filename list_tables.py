import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("TABLES:", tables)
    
    # Try to find config-like table
    for t in tables:
        if 'config' in t[0]:
            print(f"Found config table: {t[0]}")
            cursor.execute(f"SELECT * FROM {t[0]}")
            print(cursor.fetchall())
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
