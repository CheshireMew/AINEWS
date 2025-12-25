import yaml
import sqlite3
from pathlib import Path
import sys

def sync():
    print("Syncing filters.yaml to Database...")
    
    # Path setup
    base_dir = Path(__file__).parent
    yaml_path = base_dir / 'crawler' / 'config' / 'filters.yaml'
    db_path = base_dir / 'ainews.db'

    
    if not yaml_path.exists():
        print(f"ERROR: {yaml_path} not found")
        return

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"Failed to load YAML: {e}")
        return
    
    blacklist = config.get('blacklist', {})
    patterns = blacklist.get('patterns', [])
    keywords = blacklist.get('keywords', [])
    
    print(f"Found {len(patterns)} patterns and {len(keywords)} keywords in YAML.")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    added = 0
    # Clear existing? Maybe not, just insert ignore.
    # User might have added via UI.
    
    for p in patterns:
        try:
            cursor.execute("INSERT OR IGNORE INTO keyword_blacklist (keyword, match_type) VALUES (?, 'regex')", (p,))
            if cursor.rowcount > 0: added += 1
        except Exception as e:
            pass
            
    for k in keywords:
        try:
            cursor.execute("INSERT OR IGNORE INTO keyword_blacklist (keyword, match_type) VALUES (?, 'contains')", (k,))
            if cursor.rowcount > 0: added += 1
        except Exception as e:
            pass
            
    conn.commit()
    conn.close()
    print(f"Successfully synced {added} new rules to DB.")

if __name__ == "__main__":
    sync()
