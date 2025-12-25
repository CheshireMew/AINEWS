import sqlite3
import sys

conn = sqlite3.connect('ainews.db')
c = conn.cursor()
c.execute('SELECT id, title, content FROM news WHERE source_site=? ORDER BY id DESC LIMIT 1', ('blockbeats',))
row = c.fetchone()

if row:
    row_id, title, content = row
    print(f"ID: {row_id}")
    print(f"Title: {title}")
    print(f"\n{'='*60}")
    print("Content (repr - shows all characters):")
    print(f"{'='*60}")
    print(repr(content))
    print(f"\n{'='*60}")
    print("Content (actual display):")
    print(f"{'='*60}")
    print(content)
    
    # Count newlines
    newline_count = content.count('\n')
    double_newline_count = content.count('\n\n')
    triple_newline_count = content.count('\n\n\n')
    
    print(f"\n{'='*60}")
    print(f"Statistics:")
    print(f"  Total newlines (\\n): {newline_count}")
    print(f"  Double newlines (\\n\\n): {double_newline_count}")
    print(f"  Triple newlines (\\n\\n\\n): {triple_newline_count}")
else:
    print("No BlockBeats data found")

conn.close()
