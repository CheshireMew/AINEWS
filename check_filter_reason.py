import sys
import os
import re
sys.path.insert(0, os.path.join(os.getcwd(), 'crawler'))
from database.db_sqlite import Database

db = Database()
conn = db.connect()
cursor = conn.cursor()

# title to check
title = "Binance 上线吉尔吉斯索姆稳定币，该国加速推进国家级加密布局"
print(f"Checking Title: {title}")

# Fetch blacklist
cursor.execute("SELECT keyword, match_type FROM keyword_blacklist")
rules = cursor.fetchall()

print(f"Loaded {len(rules)} rules from DB.")

found = False
for r in rules:
    keyword = r['keyword']
    match_type = r['match_type']
    print(f"Checking Rule: [{match_type}] '{keyword}'")
    
    matched = False
    if match_type == 'contains':
        if keyword.lower() in title.lower():
            matched = True
    elif match_type == 'regex':
        try:
            if re.search(keyword, title, re.IGNORECASE):
                matched = True
        except:
            pass
            
    if matched:
        print(f"MATCHED Rule: '{keyword}' (Type: {match_type})")
        found = True

if not found:
    print("No DB rules matched.")

conn.close()
