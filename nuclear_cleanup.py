import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def nuclear_cleanup():
    conn = sqlite3.connect('ainews.db')
    c = conn.cursor()
    
    # 找出所有"黄金"或"gold"相关的新闻ID作为潜在的master
    c.execute("SELECT DISTINCT id FROM news WHERE title LIKE '%黄金%' OR title LIKE '%gold%'")
    all_gold_ids = [row[0] for row in c.fetchall()]
    
    print(f"找到 {len(all_gold_ids)} 个潜在的黄金/gold新闻ID: {all_gold_ids}")
    
    total_fixed = 0
    
    # 对每个黄金ID，清理其下的所有重复项
    for gid in all_gold_ids:
        c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = ?", (gid,))
        count_before = c.fetchone()[0]
        
        if count_before > 0:
            print(f"\n清理 ID {gid} 下的 {count_before} 条...")
            c.execute("""
                UPDATE news 
                SET stage='pending', is_duplicate=0, duplicate_of=NULL
                WHERE duplicate_of = ?
            """, (gid,))
            affected = c.rowcount
            total_fixed += affected
            print(f"  实际更新: {affected} 条")
    
    print(f"\n========================================")
    print(f"提交前总计修复: {total_fixed} 条")
    print(f"========================================")
    
    # 提交
    conn.commit()
    print("✅ 已提交到数据库")
    
    # 验证
    print("\n验证结果:")
    for gid in all_gold_ids:
        c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = ?", (gid,))
        remaining = c.fetchone()[0]
        if remaining > 0:
            print(f"  ID {gid}: 仍有 {remaining} 条 ❌")
        else:
            print(f"  ID {gid}: 已清空 ✅")
    
    # 验证用户报告的具体ID
    print("\n验证用户报告的ID:")
    problem_ids = [27, 28, 68, 69, 29, 30, 31]
    for pid in problem_ids:
        c.execute("SELECT duplicate_of FROM news WHERE id = ?", (pid,))
        row = c.fetchone()
        if row and row[0] is not None:
            print(f"  ID {pid}: duplicate_of={row[0]} ❌ 仍然关联")
        else:
            print(f"  ID {pid}: duplicate_of=NULL ✅ 已清理")
    
    conn.close()

if __name__ == "__main__":
    nuclear_cleanup()
