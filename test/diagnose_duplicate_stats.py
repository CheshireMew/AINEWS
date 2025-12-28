import sqlite3

conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

print("="*80)
print("诊断去重数据统计")
print("="*80)

# 1. 总新闻数
total = cursor.execute('SELECT COUNT(*) FROM news').fetchone()[0]
print(f"\n总新闻数: {total}")

# 2. 原始新闻（非duplicate）
originals = cursor.execute('SELECT COUNT(*) FROM news WHERE duplicate_of IS NULL').fetchone()[0]
print(f"原始新闻（duplicate_of IS NULL）: {originals}")

# 3. 重复新闻
duplicates = cursor.execute('SELECT COUNT(*) FROM news WHERE duplicate_of IS NOT NULL').fetchone()[0]
print(f"重复新闻（duplicate_of IS NOT NULL）: {duplicates}")

# 4. 作为master的原始新闻（有其他新闻指向它）
masters = cursor.execute('''
    SELECT COUNT(DISTINCT duplicate_of) 
    FROM news 
    WHERE duplicate_of IS NOT NULL
''').fetchone()[0]
print(f"有重复的原始新闻（作为master）: {masters}")

# 5. 独立的原始新闻（没有重复）
independent = originals - masters
print(f"独立的原始新闻（没有重复）: {independent}")

print("\n" + "="*80)
print("结论")
print("="*80)
print(f"• \"去重数据\"Tab 显示: {originals} 条（所有非duplicate新闻）")
print(f"• \"重复对照\"Tab 显示: {masters} 组（只显示有重复的master）")
print(f"• 差异: {independent} 条独立新闻不会在\"重复对照\"中显示")

conn.close()
