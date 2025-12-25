"""验证数据库清洗效果"""
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 查找包含"CryptoQuant"的新闻（刚才爬取的）
c.execute("""
    SELECT id, title, content 
    FROM news 
    WHERE source_site='blockbeats' AND content LIKE '%CryptoQuant%'
    ORDER BY id DESC 
    LIMIT 1
""")

row = c.fetchone()
if row:
    row_id, title, content = row
    print(f"数据库中的内容统计:")
    print(f"  换行符(\\n): {content.count(chr(10))}")
    print(f"  双换行(\\n\\n): {content.count(chr(10)*2)}")
    print(f"  三换行(\\n\\n\\n): {content.count(chr(10)*3)}")
    print(f"  四换行(\\n\\n\\n\\n): {content.count(chr(10)*4)}")
    
    print(f"\n内容前200字符:")
    print(content[:200])
    
    if content.count(chr(10)*2) == 0:
        print("\n✅ 清洗成功！没有多余空行")
    else:
        print("\n❌ 仍有空行")
else:
    print("未找到相关新闻")

conn.close()
