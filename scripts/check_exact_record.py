import sqlite3

conn = sqlite3.connect('ainews.db')
c = conn.cursor()

c.execute("""
    SELECT source_url, source_site, author 
    FROM news 
    WHERE source_url='https://foresightnews.pro/article/detail/93570'
""")

row = c.fetchone()
if row:
    print(f"URL: {row[0]}")
    print(f"source_site: {row[1]!r}")
    print(f"author: {row[2]!r}")
    print(f"\nLength of source_site: {len(row[1])} characters")
    print(f"Bytes of source_site: {row[1].encode('utf-8')!r}")
    print(f"\nExpected: 'ForesightNews 独家'")
    print(f"Expected bytes: {('ForesightNews 独家').encode('utf-8')!r}")
    print(f"\nMatch: {row[1] == 'ForesightNews 独家'}")
else:
    print("Record not found")
    
conn.close()
