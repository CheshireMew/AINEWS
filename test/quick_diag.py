import sys
sys.path.insert(0, '.')
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 统计所有标记为 duplicate_of=10 的新闻
c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = 10")
total = c.fetchone()[0]

# 列出前15条
c.execute("""
    SELECT id, title, published_at
    FROM news 
    WHERE duplicate_of = 10
    ORDER BY published_at DESC
    LIMIT 15
""")

with open('test/diagnosis_output.txt', 'w', encoding='utf-8') as f:
    f.write(f"共有 {total} 条新闻被标记为duplicate_of=10\n\n")
    f.write("最近的15条:\n")
    f.write("="*100 + "\n")
    
    for row in c.fetchall():
        f.write(f"ID {row[0]:4d} | {row[2]} | {row[1]}\n")

conn.close()
print(f"诊断完成，共{total}条被误标记。结果保存到 test/diagnosis_output.txt")
