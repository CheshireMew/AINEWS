"""查看SQLite数据库中的增量爬取结果"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from database import Database

def view_database():
    """查看数据库内容"""
    db = Database()
    
    print("=" * 80)
    print("数据库内容查看")
    print("=" * 80)
    
    conn = db.connect()
    cursor = conn.cursor()
    
    # 统计各网站的新闻数量
    print("\n📊 各网站新闻统计:")
    cursor.execute('''
        SELECT source_site, COUNT(*) as count
        FROM news
        GROUP BY source_site
        ORDER BY count DESC
    ''')
    
    for row in cursor.fetchall():
        print(f"   {row['source_site']:15s}: {row['count']:3d} 条")
    
    # 总数
    cursor.execute('SELECT COUNT(*) as total FROM news')
    total = cursor.fetchone()['total']
    print(f"\n   总计: {total} 条新闻")
    
    # 显示最新的10条新闻
    print("\n" + "=" * 80)
    print("最新10条新闻:")
    print("=" * 80)
    
    cursor.execute('''
        SELECT id, title, source_site, published_at, scraped_at,
               length(content) as content_length
        FROM news
        ORDER BY scraped_at DESC
        LIMIT 10
    ''')
    
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"\n[{i}] ID: {row['id']}")
        print(f"    标题: {row['title'][:60]}...")
        print(f"    来源: {row['source_site']}")
        print(f"    发布时间: {row['published_at']}")
        print(f"    抓取时间: {row['scraped_at']}")
        print(f"    内容长度: {row['content_length']} 字")
    
    # 自动导出到JSON
    print("\n" + "=" * 80)
    print("导出数据到JSON文件...")
    
    cursor.execute('SELECT * FROM news ORDER BY scraped_at DESC')
    all_news = [dict(row) for row in cursor.fetchall()]
    
    output_file = 'database_export.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_news, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"✅ 已导出 {len(all_news)} 条新闻到: {output_file}")
    
    conn.close()

if __name__ == '__main__':
    view_database()
