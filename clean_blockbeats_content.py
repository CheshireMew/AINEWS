"""清洗数据库中已有的 BlockBeats 新闻内容"""
import sqlite3
import re

def clean_existing_content():
    conn = sqlite3.connect('crawler/crypto_news.db')
    cursor = conn.cursor()
    
    # 获取所有 BlockBeats 新闻
    cursor.execute('SELECT id, content FROM news WHERE source_site = ?', ('blockbeats',))
    rows = cursor.fetchall()
    
    cleaned_count = 0
    for row_id, content in rows:
        if content:
            # 清洗内容
            cleaned = content.replace('\r\n', '\n').replace('\r', '\n')
            cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
            cleaned = cleaned.strip()
            
            # 更新数据库
            if cleaned != content:
                cursor.execute('UPDATE news SET content = ? WHERE id = ?', (cleaned, row_id))
                cleaned_count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ 已清洗 {cleaned_count} 条 BlockBeats 新闻内容")

if __name__ == '__main__':
    clean_existing_content()
