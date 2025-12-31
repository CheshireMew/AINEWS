import sys
sys.path.insert(0, r'e:\Work\Code\AINEWS')

from crawler.database.db_sqlite import Database

db = Database()
sources = db.get_all_sources()

print(f'已配置的爬虫数量: {len(sources)}\n')
print('='*80)
print('爬虫列表:')
print('='*80)

for i, source in enumerate(sources, 1):
    print(f"\n{i}. {source['name']}")
    print(f"   URL: {source['url']}")
    print(f"   类型: {source.get('type', 'news')}")
    print(f"   启用: {'是' if source.get('enabled', True) else '否'}")
    if source.get('description'):
        print(f"   描述: {source['description']}")
