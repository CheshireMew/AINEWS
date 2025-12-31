"""
批量修复 curated_news 和 deduplicated_news 表中的 type 字段
根据 source_site 判断文章类型
"""
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("批量修复 type 字段")
print("=" * 70)

# 1. 更新 curated_news 表
print("\n1. 修复 curated_news 表:")
c.execute("""
    UPDATE curated_news 
    SET type = 'article' 
    WHERE (source_site LIKE '%Article%' OR source_site LIKE '%article%')
    AND type = 'news'
""")
curated_updated = c.rowcount
print(f"   更新了 {curated_updated} 条记录: news -> article")

# 2. 更新 deduplicated_news 表
print("\n2. 修复 deduplicated_news 表:")
c.execute("""
    UPDATE deduplicated_news 
    SET type = 'article' 
    WHERE (source_site LIKE '%Article%' OR source_site LIKE '%article%')
    AND type = 'news'
""")
dedup_updated = c.rowcount
print(f"   更新了 {dedup_updated} 条记录: news -> article")

conn.commit()

# 3. 验证结果
print("\n3. 验证结果:")
c.execute("SELECT COUNT(*) FROM curated_news WHERE type = 'article'")
curated_articles = c.fetchone()[0]
print(f"   curated_news 表中的文章数: {curated_articles}")

c.execute("SELECT COUNT(*) FROM deduplicated_news WHERE type = 'article'")
dedup_articles = c.fetchone()[0]
print(f"   deduplicated_news 表中的文章数: {dedup_articles}")

conn.close()

print("\n" + "=" * 70)
print("修复完成！刷新前端页面即可看到效果。")
