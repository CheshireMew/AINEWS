import sqlite3
import os

db_path = 'ainews.db'

def check_and_clean():
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all keys to debug
    print("Listing all keys in system_config:")
    cursor.execute("SELECT key FROM system_config")
    all_rows = cursor.fetchall()
    for r in all_rows:
        print(f"  > {r[0]}")
    else:
        print("No legacy configs found.")
        
    conn.close()

if __name__ == "__main__":
    check_and_clean()
