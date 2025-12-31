from crawler.database.db_sqlite import Database

try:
    db = Database()
    prompt = db.get_config('ai_filter_prompt')
    if prompt:
        print("FOUND_PROMPT_START")
        print(prompt)
        print("FOUND_PROMPT_END")
    else:
        print("PROMPT_NOT_FOUND")
except Exception as e:
    print(f"Error: {e}")
