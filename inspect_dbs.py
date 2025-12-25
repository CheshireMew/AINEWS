
import sqlite3
import os
import glob

def inspect_dbs():
    # Find all .db files
    db_files = glob.glob('**/*.db', recursive=True)
    
    for db_path in db_files:
        print(f"\n--- Checking Database: {db_path} ---")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                print("  [Empty] No tables found.")
            
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f"SELECT count(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  Table '{table_name}': {count} rows")
                    
                    # If it looks like a news table, check columns
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    # print(f"    Columns: {', '.join(columns)}")
                    
                    if 'title' in columns:
                        cursor.execute(f"SELECT title FROM {table_name} LIMIT 3")
                        print(f"    Sample titles: {[r[0] for r in cursor.fetchall()]}")
                        
                except Exception as e:
                    print(f"  Error reading table '{table_name}': {e}")
            
            conn.close()
        except Exception as e:
            print(f"  Error connecting: {e}")

if __name__ == "__main__":
    import sys
    # Redirect stdout to a file with UTF-8 encoding
    with open('db_report.txt', 'w', encoding='utf-8') as f:
        original_stdout = sys.stdout
        sys.stdout = f
        inspect_dbs()
        sys.stdout = original_stdout
    print("Report written to db_report.txt")
