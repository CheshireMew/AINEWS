
import sqlite3
import re

def fix_ai_status():
    # 使用绝对路径
    db_path = r'e:\Work\Code\AINEWS\ainews.db'
    print(f"Connecting to {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查找所有 rejected 但分数 >= 5 的记录
        cursor.execute("SELECT id, ai_explanation, ai_status FROM curated_news WHERE ai_status = 'rejected'")
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} rejected items. Checking scores...")
        
        fixed_count = 0
        
        for row in rows:
            news_id = row[0]
            explanation = row[1]
            current_status = row[2]
            
            # 提取分数
            score = 0
            if explanation and '分' in explanation:
                try:
                    score = int(explanation.split('分')[0])
                except:
                    score = 0
            
            # 如果分数 >= 5，修正状态
            if score >= 5:
                # print(f"Fixing ID {news_id}: Score {score} >= 5, changing rejected -> approved")
                cursor.execute(
                    "UPDATE curated_news SET ai_status = 'approved' WHERE id = ?", 
                    (news_id,)
                )
                fixed_count += 1
        
        conn.commit()
        print(f"Done! Fixed {fixed_count} records.")
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_ai_status()
