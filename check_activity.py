import sqlite3
from datetime import datetime, timedelta
import collections

# Connect to database
conn = sqlite3.connect('ainews.db')
cursor = conn.cursor()

# Query recent news (last 48 hours)
query = """
SELECT source_site, published_at 
FROM news 
WHERE published_at >= datetime('now', '-48 hours')
ORDER BY published_at DESC
"""

cursor.execute(query)
rows = cursor.fetchall()
conn.close()

if not rows:
    print("No data found in the last 48 hours.")
else:
    print(f"Total rows: {len(rows)}")
    
    # Process data
    hourly_counts = collections.defaultdict(int)
    source_hourly = collections.defaultdict(lambda: collections.defaultdict(int))
    
    # Helper to parse time slightly robustly
    def parse_time(t_str):
        # Try a few formats
        formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M']
        for fmt in formats:
            try:
                return datetime.strptime(t_str.split('.')[0], fmt)
            except:
                pass
        return None

    times = []
    for source, pub_at in rows:
        dt = parse_time(pub_at)
        if dt:
            times.append(dt)
            # Round to hour
            hour_key = dt.strftime('%Y-%m-%d %H:00')
            hourly_counts[hour_key] += 1
            source_hourly[source][hour_key] += 1
    
    if times:
        print(f"Time range: {min(times)} to {max(times)}")
    
    # Sort keys
    sorted_hours = sorted(hourly_counts.keys())
    
    print("\n--- News Items Per Hour (All Sources) ---")
    # Show last 24 hours only if list is long
    start_idx = max(0, len(sorted_hours) - 24)
    for hour in sorted_hours[start_idx:]:
        print(f"{hour}: {hourly_counts[hour]}")
    
    print("\n--- News Items Per Hour by Source ---")
    sources = sorted(source_hourly.keys())
    for source in sources:
        print(f"\n{source}:")
        # Get hours for this source
        s_hours = sorted(source_hourly[source].keys())
        # Show only last 24 slots or all if scarce
        s_start = max(0, len(s_hours) - 12) 
        for hour in s_hours[s_start:]:
             print(f"  {hour}: {source_hourly[source][hour]}")
