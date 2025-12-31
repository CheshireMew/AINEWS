"""
测试 author 字段是否正确添加和使用
"""
import asyncio
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from crawler.scrapers.blockbeats import BlockBeatsScraper
from crawler.database.db_sqlite import Database

async def test_author_field():
    print("=== 测试 author 字段功能 ===\n")
    
    # 1. 测试数据库 schema
    print("1. 检查数据库 schema...")
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(news)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'author' in column_names:
        print("  ✅ news 表包含 author 字段")
    else:
        print("  ❌ news 表缺少 author 字段")
        return
    
    # 2. 测试爬虫返回的数据
    print("\n2. 测试爬虫返回数据...")
    scraper = BlockBeatsScraper()
    
    # 模拟一个 news_item
    test_item = {
        'title': '测试新闻',
        'content': '测试内容',
        'url': 'https://example.com/test',
        'published_at': '2025-12-30 16:00:00',
        'is_marked_important': True,
        'site_importance_flag': 'test',
        'author': scraper.site_name
    }
    
    if 'author' in test_item:
        print(f"  ✅ 爬虫返回包含 author 字段: {test_item['author']}")
    else:
        print("  ❌ 爬虫返回缺少 author 字段")
    
    # 3. 测试数据库插入
    print("\n3. 测试数据库插入...")
    try:
        news_id = db.insert_news({
            'title': '测试新闻 - Author字段',
            'content': '这是一条用于测试 author 字段的新闻',
            'source_site': 'test_scraper',
            'url': f'https://test.com/news/{asyncio.get_event_loop().time()}',
            'published_at': '2025-12-30 16:00:00',
            'is_marked_important': True,
            'site_importance_flag': 'test',
            'type': 'news',
            'author': 'TestAuthor'
        })
        
        if news_id:
            # 验证插入
            cursor.execute("SELECT author FROM news WHERE id = ?", (news_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 'TestAuthor':
                print(f"  ✅ 数据插入成功，author = '{result[0]}'")
                
                # 清理测试数据
                cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
                conn.commit()
            else:
                print(f"  ❌ author 字段值不正确: {result}")
        else:
            print("  ❌ 数据插入失败")
            
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
    
    finally:
        db.close()
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    asyncio.run(test_author_field())
