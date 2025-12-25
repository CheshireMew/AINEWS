import sys
from pathlib import Path
import sqlite3

# Add project root to path
sys.path.append(str(Path(__file__).parent / 'crawler'))
sys.path.append(str(Path(__file__).parent))

from database.db_sqlite import Database

def check_filters():
    print("Initialize DB...")
    db = Database()
    conn = db.connect()
    cursor = conn.cursor()
    
    # 1. Check Filtered Count
    cursor.execute("SELECT count(*) FROM news WHERE stage='filtered'")
    count = cursor.fetchone()[0]
    print(f"Total Filtered News: {count}")
    
    # 2. Check Blacklist Rules
    cursor.execute("SELECT count(*) FROM keyword_blacklist")
    rules = cursor.fetchone()[0]
    print(f"Total Blacklist Rules: {rules}")
    
    cursor.execute("SELECT id, keyword, match_type FROM keyword_blacklist LIMIT 5")
    print("Sample Rules:")
    for r in cursor.fetchall():
        print(f" - [{r[2]}] {r[1]}")
        
    # 3. Check RAW news sample
    print("\nChecking a few RAW news to see if they SHOULD have been filtered:")
    cursor.execute("SELECT id, title, content FROM news WHERE stage IN ('raw', 'deduplicated') ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    
    keywords = db.get_blacklist_keywords()
    import re
    
    for row in rows:
        title = row[1]
        text = f"{title} {row[2] or ''}".lower()
        matched = False
        reason = ""
        
        for k in keywords:
            kw = k['keyword']
            if k['match_type'] == 'regex':
                try:
                    if re.search(kw, text, re.IGNORECASE):
                        matched = True
                        reason = f"Regex: {kw}"
                        break
                except:
                    pass
            else:
                if kw.lower() in text:
                    matched = True
                    reason = f"Contains: {kw}"
                    break
        
        status = "SHOULD FILTER" if matched else "KEEP"
        print(f"ID {row[0]}: {title[:30]}... -> {status} ({reason})")

if __name__ == "__main__":
    check_filters()
