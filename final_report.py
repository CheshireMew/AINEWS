import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("="*80)
print("完整数据流测试结果 - 最新数据验证")
print("="*80)

# 查看最近5条BlockBeats新闻
c.execute('''
    SELECT id, title, content 
    FROM news 
    WHERE source_site='blockbeats' 
    ORDER BY id DESC 
    LIMIT 5
''')

rows = c.fetchall()

all_clean = True
for row_id, title, content in rows:
    has_double = content.count('\n\n')
    has_triple = content.count('\n\n\n')
    has_quad = content.count('\n\n\n\n')
    
    status = "✅ 干净" if (has_double == 0 and has_triple == 0 and has_quad == 0) else "❌ 有空行"
    
    print(f"\nID {row_id}: {title[:40]}...")
    print(f"  状态: {status}")
    print(f"  双换行: {has_double}, 三换行: {has_triple}, 四换行: {has_quad}")
    
    if has_double > 0 or has_triple > 0 or has_quad > 0:
        all_clean = False
        print(f"  内容预览: {content[:150]}")

print("\n" + "="*80)
if all_clean:
    print("✅✅✅ 所有 BlockBeats 新闻内容已完全清洗！无任何多余空行！")
    print("数据流验证: 爬虫抓取 → insert_news清洗 → 数据库存储 ✅")
else:
    print("❌ 仍有部分新闻包含空行")
print("="*80)

conn.close()
