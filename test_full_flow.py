"""测试完整数据流：爬虫 -> 清洗 -> 数据库"""
import asyncio
import sys
sys.path.insert(0, 'crawler')

from scrapers.blockbeats import BlockBeatsScraper
from database.db_sqlite import Database

async def test_flow():
    print("=== 步骤1: 爬虫抓取 ===")
    scraper = BlockBeatsScraper()
    scraper.max_items = 1
    news_list = await scraper.run()
    
    if not news_list:
        print("❌ 未抓取到新闻")
        return
    
    news = news_list[0]
    original_content = news['content']
    
    print(f"\n原始抓取内容统计:")
    print(f"  四换行(\\n\\n\\n\\n): {original_content.count(chr(10)*4)}")
    print(f"  三换行(\\n\\n\\n): {original_content.count(chr(10)*3)}")
    print(f"  双换行(\\n\\n): {original_content.count(chr(10)*2)}")
    
    print(f"\n原始内容前200字符:")
    print(original_content[:200])
    
    print(f"\n=== 步骤2: 存入数据库 (会自动清洗) ===")
    db = Database()
    
    # 添加必要字段
    if 'source_site' not in news:
        news['source_site'] = 'blockbeats'
    
    # 存入数据库（这里会触发清洗逻辑）
    news_id = db.insert_news(news)
    
    if news_id:
        print(f"✅ 成功存入数据库，ID: {news_id}")
    else:
        print(f"⚠️ 数据库返回 None（可能重复）")
    
    print(f"\n=== 步骤3: 从数据库读取验证 ===")
    import sqlite3
    conn = sqlite3.connect('ainews.db')
    c = conn.cursor()
    c.execute('SELECT content FROM news WHERE id = ?', (news_id,))
    row = c.fetchone()
    
    if row:
        db_content = row[0]
        print(f"\n数据库中的内容统计:")
        print(f"  四换行(\\n\\n\\n\\n): {db_content.count(chr(10)*4)}")
        print(f"  三换行(\\n\\n\\n): {db_content.count(chr(10)*3)}")
        print(f"  双换行(\\n\\n): {db_content.count(chr(10)*2)}")
        
        print(f"\n数据库内容前200字符:")
        print(db_content[:200])
        
        if db_content.count(chr(10)*2) == 0:
            print("\n✅ 清洗成功！数据库中无多余空行")
        else:
            print("\n❌ 清洗失败！数据库中仍有空行")
            print("\n对比:")
            print(f"  原始: {original_content.count(chr(10)*4)}个四换行, {original_content.count(chr(10)*2)}个双换行")
            print(f"  入库: {db_content.count(chr(10)*4)}个四换行, {db_content.count(chr(10)*2)}个双换行")
    
    conn.close()

asyncio.run(test_flow())
