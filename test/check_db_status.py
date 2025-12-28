#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库中 deduplicated_news 的数据状态"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_sqlite import NewsSQLiteDB

def main():
    db = NewsSQLiteDB()
    conn = db.connect()
    cursor = conn.cursor()
    
    # 检查 deduplicated_news 表的数据分布
    print("=" * 60)
    print("deduplicated_news 表数据统计:")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM deduplicated_news")
    total = cursor.fetchone()[0]
    print(f"总数据量: {total} 条\n")
    
    if total > 0:
        # 按 stage 分组统计
        cursor.execute("SELECT stage, COUNT(*) as count FROM deduplicated_news GROUP BY stage ORDER BY count DESC")
        print("按 stage 分组:")
        for row in cursor.fetchall():
            stage = row[0] or "NULL"
            count = row[1]
            print(f"  {stage:20s}: {count:5d} 条")
        
        print("\n" + "=" * 60)
        print("最近 5 条 deduplicated_news 记录:")
        print("=" * 60)
        cursor.execute("""
            SELECT id, title, stage, deduplicated_at 
            FROM deduplicated_news 
            ORDER BY deduplicated_at DESC 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"ID: {row[0]}, Stage: {row[2]}, Time: {row[3]}")
            print(f"  标题: {row[1][:60]}...")
            print()
    else:
        print("⚠️ deduplicated_news 表为空！")
        print("\n检查 news 表...")
        cursor.execute("SELECT COUNT(*) FROM news")
        news_count = cursor.fetchone()[0]
        print(f"news 表数据量: {news_count} 条")
        
        if news_count > 0:
            cursor.execute("SELECT stage, COUNT(*) FROM news GROUP BY stage")
            print("按 stage 分组:")
            for row in cursor.fetchall():
                print(f"  {row[0]:20s}: {row[1]:5d} 条")
    
    conn.close()

if __name__ == '__main__':
    main()
