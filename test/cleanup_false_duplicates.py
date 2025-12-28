"""清理被错误标记为duplicate_of=10的新闻"""
import sys
sys.path.insert(0, '.')

import sqlite3
from datetime import datetime

def backup_data():
    """备份将要修改的数据"""
    conn = sqlite3.connect('ainews.db')
    c = conn.cursor()
    
    # 导出被误标记的新闻列表
    c.execute("""
        SELECT id, title, duplicate_of, stage, is_duplicate, published_at, updated_at
        FROM news
        WHERE duplicate_of = 10
        ORDER BY id
    """)
    
    rows = c.fetchall()
    
    with open('test/backup_false_duplicates.txt', 'w', encoding='utf-8') as f:
        f.write(f"备份时间: {datetime.now()}\n")
        f.write(f"总计: {len(rows)} 条记录\n")
        f.write("="*100 + "\n\n")
        
        for row in rows:
            f.write(f"ID: {row[0]}\n")
            f.write(f"标题: {row[1]}\n")
            f.write(f"duplicate_of: {row[2]}\n")
            f.write(f"stage: {row[3]}\n")
            f.write(f"is_duplicate: {row[4]}\n")
            f.write(f"published_at: {row[5]}\n")
            f.write(f"updated_at: {row[6]}\n")
            f.write("-"*100 + "\n")
    
    conn.close()
    print(f"✅ 已备份 {len(rows)} 条记录到 test/backup_false_duplicates.txt")
    return len(rows)

def cleanup_false_duplicates():
    """清理错误的duplicate_of标记"""
    conn = sqlite3.connect('ainews.db')
    c = conn.cursor()
    
    # 清理duplicate_of=10的所有记录
    print("\n开始清理...")
    c.execute("""
        UPDATE news
        SET duplicate_of = NULL,
            is_duplicate = 0,
            stage = 'pending'
        WHERE duplicate_of = 10
    """)
    
    affected = c.rowcount
    conn.commit()
    conn.close()
    
    print(f"✅ 已清理 {affected} 条记录")
    return affected

def verify_cleanup():
    """验证清理结果"""
    conn = sqlite3.connect('ainews.db')
    c = conn.cursor()
    
    # 检查是否还有duplicate_of=10的记录
    c.execute("SELECT COUNT(*) FROM news WHERE duplicate_of = 10")
    remaining = c.fetchone()[0]
    
    # 检查ID=10的新闻状态
    c.execute("SELECT id, title, stage FROM news WHERE id = 10")
    gold = c.fetchone()
    
    conn.close()
    
    print(f"\n验证结果:")
    print(f"  剩余duplicate_of=10的记录: {remaining}")
    if gold:
        print(f"  黄金新闻(ID=10)状态: {gold[2]}")
    
    return remaining == 0

if __name__ == "__main__":
    print("="*100)
    print("清理错误的去重标记")
    print("="*100)
    
    # 1. 备份
    count = backup_data()
    
    # 2. 清理
    affected = cleanup_false_duplicates()
    
    # 3. 验证
    success = verify_cleanup()
    
    print("\n" + "="*100)
    if success:
        print("✅ 清理成功！所有误判记录已恢复为pending状态")
    else:
        print("⚠️ 清理可能未完全成功，请检查")
    print("="*100)
