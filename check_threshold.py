import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_config WHERE key = 'dedup_threshold'")
    row = cursor.fetchone()
    
    if row:
        threshold = row[0]
        print(f"当前自动去重阈值: {threshold}")
    else:
        print("未找到 dedup_threshold 配置，将使用默认值 0.50")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
