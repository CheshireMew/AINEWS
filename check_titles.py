import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 检查这几个标题
titles_to_check = [
    "贝莱德向 Coinbase 存入约 2292 枚 BTC",
    "赵长鹏：币安钱包已支持识别恶意地址",
    "某以太坊 ICO 钱包休眠 10 多年后转出 2000 枚"
]

print("检查数据库中是否有这些标题:\n")

for title in titles_to_check:
    c.execute('SELECT id, source_site, source_url FROM news WHERE title LIKE ?', (f'%{title}%',))
    rows = c.fetchall()
    
    if rows:
        print(f"✅ 找到: {title}")
        for row in rows:
            print(f"   ID: {row[0]}, 来源: {row[1]}")
            print(f"   URL: {row[2]}")
    else:
        print(f"❌ 未找到: {title}")
    print()

conn.close()
