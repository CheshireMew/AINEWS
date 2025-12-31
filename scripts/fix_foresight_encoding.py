import sqlite3
import os

db_path = 'ainews.db'

def fix_source_site():
    """修复编码混淆导致的 source_site 截断问题"""
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查找所有可能被截断的记录
    patterns = [
        ("ForesightNews 鐙%", "ForesightNews 独家"),  # 独家被错误编码
        ("ForesightNews 閫%", "ForesightNews 速递"),  # 速递可能的编码问题
        ("ForesightNews 娣?%", "ForesightNews 深度"),  # 深度可能的编码问题
    ]
    
    total_fixed = 0
    for wrong_pattern, correct_value in patterns:
        # 检查 source_site
        cursor.execute("SELECT COUNT(*) FROM news WHERE source_site LIKE ?", (wrong_pattern,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Found {count} records with source_site matching '{wrong_pattern}'")
            cursor.execute("UPDATE news SET source_site = ? WHERE source_site LIKE ?", 
                          (correct_value, wrong_pattern))
            print(f"  → Fixed to '{correct_value}'")
            total_fixed += cursor.rowcount
            
        # 也检查 author 字段
        cursor.execute("SELECT COUNT(*) FROM news WHERE author LIKE ?", (wrong_pattern,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"Found {count} records with author matching '{wrong_pattern}'")
            cursor.execute("UPDATE news SET author = ? WHERE author LIKE ?",
                          (correct_value, wrong_pattern))
            print(f"  → Fixed author to '{correct_value}'")
            total_fixed += cursor.rowcount
    
    conn.commit()
    print(f"\nTotal records fixed: {total_fixed}")
    
    # 验证修复结果
    print("\n=== Verification ===")
    cursor.execute('''
        SELECT source_site, COUNT(*) 
        FROM news 
        WHERE source_site LIKE 'ForesightNews%'
        GROUP BY source_site
    ''')
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} records")
        
    conn.close()

if __name__ == "__main__":
    fix_source_site()
