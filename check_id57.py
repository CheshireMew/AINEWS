import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 查看ID 57的内容
c.execute('SELECT id, title, content FROM news WHERE id = 57')
row = c.fetchone()

if row:
    row_id, title, content = row
    print(f"ID: {row_id}")
    print(f"Title: {title[:60]}")
    
    print(f"\n内容统计:")
    print(f"  总换行符: {content.count(chr(10))}")
    print(f"  双换行(\\n\\n): {content.count(chr(10)*2)}")
    print(f"  三换行(\\n\\n\\n): {content.count(chr(10)*3)}")
    print(f"  四换行(\\n\\n\\n\\n): {content.count(chr(10)*4)}")
    
    if content.count(chr(10)*2) == 0:
        print("\n✅✅✅ 完美！数据流清洗成功！数据库中无任何多余空行！")
    else:
        print(f"\n❌ 仍有问题: {content.count(chr(10)*2)}个双换行")
    
    print(f"\n内容显示 (前300字符):")
    print(content[:300])
else:
    print("未找到ID 57")

conn.close()
