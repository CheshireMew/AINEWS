import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# 查询所有字段
cursor.execute('''
    SELECT * 
    FROM curated_news 
    WHERE push_status = 'sent' AND type = 'article' 
    LIMIT 1
''')

# 获取列名
columns = [description[0] for description in cursor.description]
print("所有列名:")
print(columns)
print("\n")

# 查询数据
cursor.execute('''
    SELECT id, title, ai_status, ai_score, ai_explanation, ai_summary, ai_category
    FROM curated_news 
    WHERE push_status = 'sent' AND type = 'article' 
    LIMIT 3
''')

rows = cursor.fetchall()
for r in rows:
    print(f'ID: {r[0]}')
    print(f'Title: {r[1][:50]}...')
    print(f'ai_status: {r[2]}')
    print(f'ai_score: {r[3]}')
    print(f'ai_explanation: {r[4]}')
    print(f'ai_summary: {r[5]}')
    print(f'ai_category: {r[6]}')
    print('---')

conn.close()
