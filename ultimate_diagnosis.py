import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def ultimate_diagnosis():
    conn = sqlite3.connect('ainews.db')
    c = conn.cursor()
    
    # 1. 检查用户报告的具体ID
    problem_ids = [27, 28, 68, 69, 29, 30, 31]
    print("=== 用户报告的问题ID当前状态 ===")
    for pid in problem_ids:
        c.execute("""
            SELECT n.id, n.stage, n.duplicate_of, n.is_duplicate, m.title
            FROM news n
            LEFT JOIN news m ON n.duplicate_of = m.id
            WHERE n.id = ?
        """, (pid,))
        row = c.fetchone()
        if row:
            print(f"\nID {row[0]}:")
            print(f"  stage: {row[1]}")
            print(f"  duplicate_of: {row[2]}")
            print(f"  is_duplicate: {row[3]}")
            if row[4]:
                print(f"  Master: {row[4][:50]}")
    
    # 2. 找出ALL "黄金"相关新闻
    print("\n\n=== 所有包含'黄金'的新闻 ===")
    c.execute("SELECT id, title FROM news WHERE title LIKE '%黄金%'")
    all_gold = c.fetchall()
    for row in all_gold:
        c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = ?", (row[0],))
        child_count = c.fetchone()[0]
        print(f"ID {row[0]}: {row[1]}")
        if child_count > 0:
            print(f"  -> {child_count} 条新闻链接到此ID ⚠️")
    
    # 3. 找出ALL "gold"相关新闻（英文）
    print("\n\n=== 所有包含'gold'的新闻 ===")
    c.execute("SELECT id, title FROM news WHERE title LIKE '%gold%'")
    all_gold_en = c.fetchall()
    for row in all_gold_en:
        c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = ?", (row[0],))
        child_count = c.fetchone()[0]
        print(f"ID {row[0]}: {row[1]}")
        if child_count > 0:
            print(f"  -> {child_count} 条新闻链接到此ID ⚠️")
    
    conn.close()

if __name__ == "__main__":
    ultimate_diagnosis()
