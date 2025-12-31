from crawler.database.db_sqlite import Database

def test_query():
    db = Database()
    print("Testing get_deduplicated_news with type='article' and stage='verified'...")
    try:
        result = db.get_deduplicated_news(page=1, limit=10, type_filter='article', stage='verified')
        print(f"Total: {result['total']}")
        print(f"Data Length: {len(result['data'])}")
        if len(result['data']) > 0:
            print("First Item Title:", result['data'][0]['title'])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_query()
