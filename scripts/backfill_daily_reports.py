
import os
import sys
import sqlite3
import datetime
import html

# Add backend directory to sys.path to ensure we can import any necessary modules if needed,
# though here we might just use direct SQLite for simplicity script.
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'ainews.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def backfill_articles(conn, date_str):
    """
    Backfill Daily Articles for a specific date (00:00 to 23:59).
    Logic intersects with auto_daily_article_push: score > 0
    """
    cursor = conn.cursor()
    
    # Calculate time range for that specific day
    start_time = f"{date_str} 00:00:00"
    end_time = f"{date_str} 23:59:59"
    
    # Query Articles
    query = """
        SELECT title, source_url, ai_explanation
        FROM curated_news 
        WHERE published_at BETWEEN ? AND ?
        AND type = 'article'
        AND ai_status IN ('approved', 'rejected') 
        ORDER BY published_at DESC
    """
    cursor.execute(query, (start_time, end_time))
    rows = cursor.fetchall()
    
    news_list = []
    for row in rows:
        title, url, explanation = row
        explanation = explanation or ""
        score = 0
        if explanation and '分' in explanation:
            try:
                score = int(explanation.split('分')[0])
            except:
                score = 0
        
        # Article threshold: score > 0 (as per main.py)
        if score > 0:
            news_list.append({
                'title': title,
                'source_url': url,
                'score': score
            })
    
    if not news_list:
        print(f"  [Article] No items for {date_str}")
        return

    # Generate HTML content
    print(f"  [Article] Found {len(news_list)} items for {date_str}")
    formatted_items = []
    for news in news_list:
        title = news.get('title', "No Title")
        url = news.get('source_url', "")
        safe_title = html.escape(title)
        line = f"📰 <a href=\"{url}\">{safe_title}</a>"
        formatted_items.append(line)
        
    base_header = f"📅 <b>{date_str} 深度文章日报</b>\n\n"
    report_content = base_header + "\n\n".join(formatted_items)
    report_content += '\n\n🤖 由 <a href="https://t.me/CheshireBTC">AINEWS</a> 自动生成'
    
    # Insert into DB
    cursor.execute("""
        INSERT OR REPLACE INTO daily_reports 
        (date, type, title, content, news_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, 'article', f'{date_str} 深度文章日报', report_content, len(news_list), f"{date_str} 21:00:00"))
    conn.commit()
    print(f"  [Article] Saved report for {date_str}")

def backfill_news(conn, date_str):
    """
    Backfill Daily News for a specific date.
    Logic intersects with auto_daily_best_push: score >= 5
    """
    cursor = conn.cursor()
    
    start_time = f"{date_str} 00:00:00"
    end_time = f"{date_str} 23:59:59"
    
    # Query News
    query = """
        SELECT title, source_url, ai_explanation
        FROM curated_news 
        WHERE published_at BETWEEN ? AND ?
        AND type = 'news'
        AND ai_status IS NOT NULL
        ORDER BY published_at DESC
    """
    cursor.execute(query, (start_time, end_time))
    rows = cursor.fetchall()
    
    news_list = []
    for row in rows:
        title, url, explanation = row
        explanation = explanation or ""
        score = 0
        if explanation and '分' in explanation:
            try:
                score = int(explanation.split('分')[0])
            except:
                score = 0
        
        # News threshold: score >= 5 (as per main.py)
        if score >= 5:
            news_list.append({
                'title': title,
                'source_url': url,
                'score': score
            })
            
    # Sort by score desc
    news_list.sort(key=lambda x: x['score'], reverse=True)
    
    if not news_list:
        print(f"  [News] No items for {date_str}")
        return

    # Generate HTML content
    print(f"  [News] Found {len(news_list)} items for {date_str}")
    formatted_items = []
    for news in news_list:
        title = news.get('title', "No Title")
        url = news.get('source_url', "")
        safe_title = html.escape(title)
        line = f"<a href=\"{url}\">{safe_title}</a>"
        formatted_items.append(line)
        
    base_header = f"📅 <b>{date_str} 精选日报 (Score>=5)</b>\n\n"
    report_content = base_header + "\n\n".join(formatted_items)
    report_content += '\n\n🤖 由 <a href="https://t.me/CheshireBTC">AINEWS</a> 自动生成'
    
    cursor.execute("""
        INSERT OR REPLACE INTO daily_reports 
        (date, type, title, content, news_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date_str, 'news', f'{date_str} 精选日报', report_content, len(news_list), f"{date_str} 21:00:00"))
    conn.commit()
    print(f"  [News] Saved report for {date_str}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = get_connection()
    
    # Backfill last 5 days
    today = datetime.date.today()
    for i in range(5):
        target_date = today - datetime.timedelta(days=i)
        date_str = target_date.strftime('%Y-%m-%d')
        print(f"Processing {date_str}...")
        
        backfill_articles(conn, date_str)
        backfill_news(conn, date_str)
        
    conn.close()
    print("Backfill complete.")

if __name__ == "__main__":
    main()
