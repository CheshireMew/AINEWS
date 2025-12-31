import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    # Check tables again
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("ALL_TABLES:", tables)
    
    # Check schema of config (matches fuzzy)
    target_table = None
    for t in tables:
        if 'config' in t[0]:
            target_table = t[0]
            print(f"Targeting table: '{target_table}'")
            break
            
    if target_table:
        cursor.execute(f"PRAGMA table_info({target_table})")
        columns = cursor.fetchall()
        print("COLUMNS:", columns)
        
        cursor.execute(f"SELECT * FROM {target_table}")
        rows = cursor.fetchall()
        print("ROWS:", rows)
    else:
        print("Config table not found")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
