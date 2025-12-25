"""查看数据库中 BlockBeats 新闻的实际内容"""
import sqlite3

# 尝试多个可能的数据库路径
db_paths = [
    'ainews.db',
    'crawler/ainews.db', 
    'crawler/crypto_news.db'
]

for db_path in db_paths:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取最新的 BlockBeats 新闻
        cursor.execute('''
            SELECT id, title, content 
            FROM news 
            WHERE source_site = ? 
            ORDER BY id DESC 
            LIMIT 3
        ''', ('blockbeats',))
        
        rows = cursor.fetchall()
        
        if rows:
            print(f"\n✅ 数据库: {db_path}")
            print(f"找到 {len(rows)} 条 BlockBeats 新闻\n")
            
            for row_id, title, content in rows:
                print(f"{'='*80}")
                print(f"ID: {row_id}")
                print(f"标题: {title[:50]}...")
                print(f"\n内容 (repr):")
                print(repr(content))
                print(f"\n内容 (原始):")
                print(content)
                print(f"{'='*80}\n")
            
            conn.close()
            break
        else:
            conn.close()
            
    except Exception as e:
        print(f"尝试 {db_path}: {e}")
        continue
else:
    print("❌ 未找到包含 BlockBeats 数据的数据库")
