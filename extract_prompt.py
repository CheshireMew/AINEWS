import sqlite3
import os

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'ai_filter_prompt'")
    row = cursor.fetchone()
    if row:
        print("FOUND_PROMPT_START")
        print(row[0])
        print("FOUND_PROMPT_END")
    else:
        print("PROMPT_NOT_FOUND")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
