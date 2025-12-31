import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM config")
    rows = cursor.fetchall()
    print("CONFIG_START")
    for r in rows:
        print(f"Key: {r[0]}, Value: {r[1]}")
    print("CONFIG_END")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
