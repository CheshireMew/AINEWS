import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

cursor.execute("SELECT value FROM system_config WHERE key='dedup_threshold'")
row = cursor.fetchone()
if row:
    print(f'\n当前保存的去重阈值: {row[0]}')
else:
    print('\n未设置去重阈值（使用默认0.50）')

conn.close()
