import sqlite3
import pandas as pd
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_stuck():
    try:
        conn = sqlite3.connect('ainews.db')
        
        print("--- Checking items with stage='duplicate' ---")
        df = pd.read_sql_query("SELECT id, title, stage, duplicate_of, published_at FROM news WHERE stage='duplicate'", conn)
        
        if df.empty:
            print("No items with stage='duplicate' found.")
        else:
            print(f"Found {len(df)} items:")
            print(df.to_string())
            
        print("\n--- Checking items with stage='pending' (Potential Limbo) ---")
        df_pending = pd.read_sql_query("SELECT id, title, stage, duplicate_of, published_at FROM news WHERE stage='pending' LIMIT 20", conn)
        if not df_pending.empty:
             print(f"Found {len(df_pending)} pending items (showing first 20):")
             print(df_pending.to_string())
             
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_stuck()
