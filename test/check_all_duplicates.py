import sqlite3

def check_duplicates(master_id):
    conn = sqlite3.connect('ainews.db')
    cursor = conn.cursor()
    
    print(f"--- Checking Duplicates for Master ID {master_id} ---")
    cursor.execute("SELECT id, title, published_at FROM news WHERE duplicate_of = ?", (master_id,))
    rows = cursor.fetchall()
    
    if not rows:
        print("No duplicates found.")
    else:
        for row in rows:
            print(f"ID: {row[0]}, Pub: {row[2]}")
            print(f"Title: {row[1]}")
            
    conn.close()

if __name__ == "__main__":
    check_duplicates(1271)
