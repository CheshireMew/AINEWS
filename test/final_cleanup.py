"""清理数据库并准备walkthrough"""
import sys
sys.path.insert(0, '.')
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

print("="*100)
print("清理数据库中的误判记录")
print("="*100)

# 检查所有duplicate_of不为NULL的记录
c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of IS NOT NULL")
total_dups = c.fetchone()[0]
print(f"\n当前标记为重复的记录数: {total_dups}")

if total_dups > 0:
    print("\n重置所有重复标记...")
    c.execute("""
        UPDATE news
        SET duplicate_of = NULL,
            is_duplicate = 0,
            stage = 'pending'
        WHERE duplicate_of IS NOT NULL
    """)
    
    affected = c.rowcount
    conn.commit()
    print(f"✅ 已清理 {affected} 条记录")
else:
    print("✅ 没有需要清理的记录")

conn.close()

print("\n" + "="*100)
print("准备就绪！现在可以:")
print("1. 在前端重新触发去重操作")
print("2. 观察Sonic vs ZEC是否还会被误判")
print("="*100)
