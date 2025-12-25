"""测试SQLite数据库功能"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_sqlite():
    """测试SQLite数据库"""
    print("=" * 60)
    print("测试SQLite数据库")
    print("=" * 60)
    
    # 导入Database（会自动选择SQLite）
    from database import Database
    
    print("\n1. 初始化数据库...")
    db = Database()
    print("✅ 数据库初始化成功")
    
    print("\n2. 测试插入新闻...")
    news_data = {
        'title': 'SQLite测试新闻',
        'content': '这是一条测试新闻内容',
        'source_site': 'test',
        'url': f'https://test.com/news/test_{int(__import__("time").time())}',
        'published_at': __import__("datetime").datetime.now(),
        'is_marked_important': True,
        'site_importance_flag': 'test_flag'
    }
    
    news_id = db.insert_news(news_data)
    if news_id:
        print(f"✅ 新闻插入成功，ID: {news_id}")
    else:
        print("❌ 新闻插入失败")
        return False
    
    print("\n3. 测试get_latest_news()...")
    latest = db.get_latest_news('test')
    if latest:
        print(f"✅ 获取最新新闻成功")
        print(f"   标题: {latest['title']}")
        print(f"   URL: {latest['source_url']}")
    else:
        print("❌ 获取最新新闻失败")
        return False
    
    print("\n4. 测试get_news_by_stage()...")
    news_list = db.get_news_by_stage('raw', limit=10)
    print(f"✅ 获取到 {len(news_list)} 条raw阶段的新闻")
    
    print("\n5. 测试update_news()...")
    db.update_news(news_id, {
        'stage': 'keyword_filtered',
        'keyword_filter_passed': True
    })
    print("✅ 新闻更新成功")
    
    print("\n6. 测试log_processing()...")
    db.log_processing(news_id, 'test', 'test_action', '测试日志')
    print("✅ 日志记录成功")
    
    print("\n7. 测试标签功能...")
    tag_id = db.insert_or_get_tag('测试标签', 'test')
    print(f"✅ 标签ID: {tag_id}")
    
    db.associate_tags(news_id, [tag_id])
    print("✅ 标签关联成功")
    
    print("\n" + "=" * 60)
    print("✅ 所有SQLite数据库功能测试通过！")
    print("=" * 60)
    
    # 显示数据库文件位置
    db_path = Path(__file__).parent.parent / 'ainews.db'
    print(f"\n📁 数据库文件: {db_path}")
    print(f"📊 数据库大小: {db_path.stat().st_size / 1024:.2f} KB")
    
    return True

if __name__ == '__main__':
    success = test_sqlite()
    sys.exit(0 if success else 1)
