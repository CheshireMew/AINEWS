import sqlite3
import os

db_path = 'ainews.db'

def migrate_foresight_data():
    if not os.path.exists(db_path):
        print("DB not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Starting migration of Foresight records...")
    
    # 1. ForesightNews 深度
    cursor.execute('''
        UPDATE news 
        SET source_site = 'ForesightNews 深度' 
        WHERE source_site = 'ForesightNews Article' AND author = 'ForesightNews 深度'
    ''')
    print(f"Migrated {cursor.rowcount} records to 'ForesightNews 深度'")
    
    # 2. ForesightNews 独家
    cursor.execute('''
        UPDATE news 
        SET source_site = 'ForesightNews 独家' 
        WHERE source_site = 'ForesightNews Article' AND author = 'ForesightNews 独家'
    ''')
    print(f"Migrated {cursor.rowcount} records to 'ForesightNews 独家'")
    
    # 3. ForesightNews 速递
    cursor.execute('''
        UPDATE news 
        SET source_site = 'ForesightNews 速递' 
        WHERE source_site = 'ForesightNews Article' AND author = 'ForesightNews 速递'
    ''')
    print(f"Migrated {cursor.rowcount} records to 'ForesightNews 速递'")
    
    # 4. 佐爷歪脖山
    cursor.execute('''
        UPDATE news 
        SET source_site = '佐爷歪脖山' 
        WHERE source_site = 'ForesightNews Article' AND author = '佐爷歪脖山'
    ''')
    print(f"Migrated {cursor.rowcount} records to '佐爷歪脖山'")
    
    conn.commit()
    print("Migration complete.")
    conn.close()

if __name__ == "__main__":
    migrate_foresight_data()
