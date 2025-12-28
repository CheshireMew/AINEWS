import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("诊断孤儿duplicate记录（duplicate_of指向不存在的ID）")
print("="*80)

# 查找孤儿记录
orphan_query = '''
    SELECT n1.id, n1.title, n1.duplicate_of
    FROM news n1
    LEFT JOIN news n2 ON n1.duplicate_of = n2.id
    WHERE n1.duplicate_of IS NOT NULL 
      AND n2.id IS NULL
'''

orphans = cursor.execute(orphan_query).fetchall()

if orphans:
    print(f"\n❌ 发现 {len(orphans)} 条孤儿记录:")
    for news_id, title, master_id in orphans[:10]:
        print(f"  ID {news_id} → 不存在的Master ID {master_id}")
        print(f"    标题: {title[:60]}")
    
    if len(orphans) > 10:
        print(f"  ... 还有 {len(orphans) - 10} 条")
    
    # 提供修复选项
    print("\n" + "="*80)
    print("修复方案：清理这些孤儿记录的duplicate_of，恢复为原始状态")
    print("="*80)
    
    response = input("\n是否执行清理？(y/n): ")
    if response.lower() == 'y':
        cursor.execute('''
            UPDATE news 
            SET duplicate_of = NULL, 
                is_local_duplicate = 0,
                duplicate_reason = NULL
            WHERE duplicate_of IS NOT NULL 
              AND duplicate_of NOT IN (SELECT id FROM news)
        ''')
        conn.commit()
        print(f"\n✅ 已清理 {cursor.rowcount} 条孤儿记录")
    else:
        print("\n❌ 取消清理")
else:
    print("\n✅ 没有发现孤儿记录")

conn.close()
