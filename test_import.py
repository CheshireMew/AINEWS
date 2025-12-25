import sys
sys.path.insert(0, 'crawler')

try:
    print("Testing import...")
    from database.db_sqlite import Database
    print("✅ Database imported")
    
    print("Testing backend main...")
    import backend.main
    print("✅ Backend main imported")
    
except Exception as e:
    import traceback
    print(f"❌ Error: {e}")
    traceback.print_exc()
