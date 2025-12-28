import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("手动执行还原去重数据")
print("="*80)

# 1. 重置所有有duplicate_of的新闻
print("\n1. 重置duplicate状态的新闻...")
cursor.execute("""
    UPDATE news 
    SET duplicate_of = NULL
    WHERE duplicate_of IS NOT NULL
""")
dup_count = cursor.rowcount
print(f"   ✓ 清理了 {dup_count} 条duplicate_of记录")

# 2. 处理deduplicated_news表
print("\n2. 处理deduplicated_news表...")
cursor.execute("SELECT id, original_news_id FROM deduplicated_news")
dedup_rows = cursor.fetchall()
processed_count = len(dedup_rows)
print(f"   找到 {processed_count} 条deduplicated_news记录")

if processed_count > 0:
    news_ids = [row[1] for row in dedup_rows if row[1]]
    if news_ids:
        placeholders = ','.join(['?'] * len(news_ids))
        cursor.execute(f"""
            UPDATE news 
            SET stage = 'raw'
            WHERE id IN ({placeholders})
        """, news_ids)
        raw_count = cursor.rowcount
        print(f"   ✓ 更新了 {raw_count} 条news为raw状态")
    
    cursor.execute("DELETE FROM deduplicated_news")
    del_count = cursor.rowcount
    print(f"   ✓ 删除了 {del_count} 条deduplicated_news记录")

# 提交
conn.commit()

# 3. 验证结果
print("\n3. 验证还原结果...")
total = cursor.execute('SELECT COUNT(*) FROM news').fetchone()[0]
duplicates = cursor.execute('SELECT COUNT(*) FROM news WHERE duplicate_of IS NOT NULL').fetchone()[0]
dedup_table = cursor.execute('SELECT COUNT(*) FROM deduplicated_news').fetchone()[0]
raw_stage = cursor.execute('SELECT COUNT(*) FROM news WHERE stage = "raw"').fetchone()[0]

print(f"   总新闻数: {total}")
print(f"   剩余duplicate_of: {duplicates} (应该为0)")
print(f"   剩余deduplicated_news: {dedup_table} (应该为0)")
print(f"   raw状态新闻: {raw_stage}")

conn.close()

print("\n" + "="*80)
if duplicates == 0 and dedup_table == 0:
    print("✅ 还原成功！所有数据已恢复")
else:
    print("❌ 还原未完全成功，请检查")
print("="*80)
