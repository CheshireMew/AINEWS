"""清洗数据库中所有新闻的内容（移除多余空行）"""
import sqlite3
import re

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 获取所有新闻
cursor.execute('SELECT id, content, source_site FROM news WHERE content IS NOT NULL')
rows = cursor.fetchall()

print(f"找到 {len(rows)} 条新闻需要检查")

cleaned_count = 0
for row_id, content, source in rows:
    if content:
        # 清洗内容 - 移除所有多余空行
        cleaned = content.replace('\r\n', '\n').replace('\r', '\n')
        # 关键：将所有连续的换行+空白+换行 替换为单个换行
        cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
        cleaned = cleaned.strip()
        
        # 只有实际改变了才更新
        if cleaned != content:
            cursor.execute('UPDATE news SET content = ? WHERE id = ?', (cleaned, row_id))
            cleaned_count += 1
            if cleaned_count <= 5:  # 只打印前5个
                print(f"  清洗 #{row_id} ({source})")

conn.commit()
conn.close()

print(f"\n✅ 共清洗了 {cleaned_count} 条新闻内容")
print("所有多余空行已移除！")
