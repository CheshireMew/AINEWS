import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 查找黄金新闻
print("=== 查找黄金新闻 ===")
cursor.execute("SELECT id, title FROM news WHERE title LIKE '%现货黄金今晨涨破%'")
gold_news = cursor.fetchall()
for row in gold_news:
    print(f"ID {row[0]}: {row[1]}")
    gold_id = row[0]

# 检查问题新闻的状态
print("\n=== 检查问题新闻 ===")
problem_ids = [1160, 1163, 1161, 1159, 1153, 1154]
for news_id in problem_ids:
    cursor.execute("SELECT id, title, duplicate_of FROM news WHERE id = ?", (news_id,))
    row = cursor.fetchone()
    if row:
        print(f"ID {row[0]}: {row[1][:60]}")
        print(f"  -> duplicate_of: {row[2]}")
    else:
        print(f"ID {news_id}: 未找到")

conn.close()
