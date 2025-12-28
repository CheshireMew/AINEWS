import sys
sys.path.insert(0, '.')
import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

# 再次清理所有duplicate_of=10的记录
c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = 10")
count_before = c.fetchone()[0]

print(f"清理前：{count_before} 条记录被误标记为duplicate_of=10")

if count_before > 0:
    print("正在清理...")
    c.execute("""
        UPDATE news
        SET duplicate_of = NULL,
            is_duplicate = 0,
            stage = 'pending'
        WHERE duplicate_of = 10
    """)
    
    affected = c.rowcount
    conn.commit()
    print(f"✅ 已清理 {affected} 条记录")
else:
    print("✅ 没有需要清理的记录")

conn.close()
print("\n重要提示：")
print("1. 后端服务器已经在运行新代码")
print("2. 请在前端重新触发去重操作来测试修复效果")
print("3. 不要使用旧的去重结果")
