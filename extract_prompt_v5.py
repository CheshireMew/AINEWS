import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    # Try multiple possible keys
    keys = ['ai_filter_prompt', 'ai_filter_prompt_news']
    
    print("SEARCH_START")
    for k in keys:
        cursor.execute("SELECT value FROM system_config WHERE key = ?", (k,))
        row = cursor.fetchone()
        if row:
            print(f"KEY: {k}")
            with open('recovered_prompt.txt', 'w', encoding='utf-8') as f:
                f.write(row[0])
            print("Prompt saved to recovered_prompt.txt")
    print("SEARCH_END")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
