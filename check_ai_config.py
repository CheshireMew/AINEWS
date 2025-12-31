import sqlite3

try:
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    # 查询所有AI相关配置
    cursor.execute("SELECT key, value FROM system_config WHERE key LIKE 'ai_filter_prompt%'")
    rows = cursor.fetchall()
    
    print("=== AI 筛选配置 ===")
    if rows:
        for key, value in rows:
            print(f"\n配置项: {key}")
            print(f"提示词: {value[:100]}..." if len(value) > 100 else f"提示词: {value}")
    else:
        print("未找到任何 AI 筛选配置")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
