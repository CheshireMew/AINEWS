import sqlite3
import os
from datetime import datetime, timedelta

def check_config():
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    # 1. Check Config
    cursor.execute("SELECT value FROM system_config WHERE key='auto_deduplication_hours' OR key='auto_dedup_hours'")
    row = cursor.fetchone()
    config_hours = int(row[0]) if row else 2
    print(f"Current Auto Dedup Hours: {config_hours}")
    
    # 2. Check Time Window
    now = datetime.now()
    cutoff = now - timedelta(hours=config_hours)
    print(f"Current Time: {now}")
    print(f"Cutoff Time: {cutoff}")
    
    # 3. Check Target News
    target_time = datetime(2025, 12, 28, 14, 59, 0)
    print(f"News Time:   {target_time}")
    
    if target_time < cutoff:
        print("❌ NEWS IS TOO OLD! It will be ignored by auto_deduplication.")
    else:
        print("✅ News is within window.")
    
    conn.close()

if __name__ == "__main__":
    check_config()
