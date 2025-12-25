import sys
import os
import importlib.util
from datetime import datetime

print("Testing Database Insertion...")
try:
    # Import db_sqlite dynamically
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crawler/database/db_sqlite.py')
    spec = importlib.util.spec_from_file_location("db_sqlite", db_path)
    db_pkg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_pkg)
    Database = db_pkg.Database

    db = Database()
    print(f"DB Path from instance: {db.db_path}")
    
    test_item = {
        'title': f'Test Item {datetime.now().isoformat()}',
        'content': 'Test Content',
        'source_site': 'odaily',
        'url': f'http://test.com/{datetime.now().timestamp()}',
        'published_at': datetime.now().isoformat()
    }
    
    res = db.insert_news(test_item)
    print(f"Insert Result ID: {res}")
    
    if res:
        print("Insert successful. Checking DB...")
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM news WHERE id = ?", (res,))
        row = cursor.fetchone()
        if row:
            print(f"Found row: {row['id']} - {row['title']}")
        else:
            print("Row NOT found after insert!")
        conn.close()
    else:
        print("Insert failed (Duplicate or Error).")
        
except Exception as e:
    print(f"Test Failed: {e}")
