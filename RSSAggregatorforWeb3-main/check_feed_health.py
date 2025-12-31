import xml.etree.ElementTree as ET
import asyncio
import aiohttp
import feedparser
import datetime
import time
from urllib.parse import urlparse
import sys

# Windows ProactorEventLoop policy for better async performance on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

OPML_FILE = 'RAW.opml'
REPORT_FILE = 'FEED_HEALTH_REPORT.md'
CONCURRENCY = 50  # Number of concurrent requests

def parse_opml(file_path):
    feeds = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        for outline in root.iter('outline'):
            if outline.get('type') == 'rss' and outline.get('xmlUrl'):
                # Try to get the category (parent outline text)
                category = "Uncategorized"
                # This is a simple way to find parent, might not work in all ElementTree versions cleanly for iter
                # simpler approach: rely on the structure we know
                pass 
                
        # Re-parse to get hierarchy correctly
        root = tree.getroot()
        body = root.find('body')
        for category_outline in body.findall('outline'):
            category_name = category_outline.get('text') or category_outline.get('title') or "Uncategorized"
            for feed_outline in category_outline.findall('outline'):
                 if feed_outline.get('type') == 'rss' and feed_outline.get('xmlUrl'):
                     feeds.append({
                         'title': feed_outline.get('text') or feed_outline.get('title'),
                         'url': feed_outline.get('xmlUrl'),
                         'category': category_name
                     })
    except Exception as e:
        print(f"Error parsing OPML: {e}")
    return feeds

async def fetch_feed(session, feed_info):
    url = feed_info['url']
    status = 'Unknown'
    last_updated = None
    error_msg = None
    days_since_update = 9999

    try:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                content = await response.read()
                parsed = feedparser.parse(content)
                
                if parsed.bozo and not parsed.entries:
                     status = 'Error'
                     error_msg = f"Parse Error: {parsed.bozo_exception}"
                else:
                    # Find latest date
                    latest_date = None
                    
                    # Check feed.updated_parsed
                    if hasattr(parsed.feed, 'updated_parsed') and parsed.feed.updated_parsed:
                        latest_date = parsed.feed.updated_parsed
                    
                    # Check entries
                    if parsed.entries:
                        for entry in parsed.entries:
                            entry_date = None
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                entry_date = entry.published_parsed
                            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                                entry_date = entry.updated_parsed
                            
                            if entry_date:
                                if latest_date is None or entry_date > latest_date:
                                    latest_date = entry_date
                    
                    if latest_date:
                        last_updated = datetime.datetime.fromtimestamp(time.mktime(latest_date))
                        days_since_update = (datetime.datetime.now() - last_updated).days
                        
                        if days_since_update <= 30:
                            status = 'Active'
                        elif days_since_update <= 90:
                            status = 'Recent'
                        elif days_since_update <= 365:
                            status = 'Stale'
                        else:
                            status = 'Inactive'
                    else:
                        status = 'No Date Found'
                        # Treat 'No Date Found' but successfully parsed as potentially active if headers suggest? 
                        # simplicity: Keep as No Date Found
            else:
                status = 'Error'
                error_msg = f"HTTP {response.status}"
    except Exception as e:
        status = 'Error'
        error_msg = str(e)

    return {
        **feed_info,
        'status': status,
        'days_since_update': days_since_update,
        'last_updated': last_updated,
        'error': error_msg
    }

async def main():
    print(f"Parsing {OPML_FILE}...")
    feeds = parse_opml(OPML_FILE)
    print(f"Found {len(feeds)} feeds. Checking health with {CONCURRENCY} concurrent workers...")

    async with aiohttp.ClientSession() as session:
        tasks = []
        results = []
        
        # Process in chunks to show progress
        total = len(feeds)
        for i in range(0, total, CONCURRENCY):
            batch = feeds[i:i+CONCURRENCY]
            batch_tasks = [fetch_feed(session, feed) for feed in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            print(f"Processed {min(i+CONCURRENCY, total)}/{total} feeds...")

    # generate report
    stats = {
        'Active': 0, 'Recent': 0, 'Stale': 0, 'Inactive': 0, 'Error': 0, 'No Date Found': 0, 'Total': len(results)
    }
    
    # Sort results
    # Priority: Error -> Active -> ... for list view? 
    # Actually user likely wants to know what works.
    # Let's group by category in the report.
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# RSS Feed Health Report\n\n")
        f.write(f"Generated on: {datetime.datetime.now().isoformat()}\n\n")
        
        # Statistics
        for r in results:
            stats[r['status']] += 1
            
        f.write("## 统计概览 (Statistics)\n\n")
        f.write("| Status | Count | Description |\n")
        f.write("|--------|-------|-------------|\n")
        f.write(f"| **Active** | {stats['Active']} | Updated within 30 days |\n")
        f.write(f"| **Recent** | {stats['Recent']} | Updated within 90 days |\n")
        f.write(f"| **Stale** | {stats['Stale']} | Updated within 1 year |\n")
        f.write(f"| **Inactive** | {stats['Inactive']} | No updates for > 1 year |\n")
        f.write(f"| **No Date** | {stats['No Date Found']} | Parsed but no dates found |\n")
        f.write(f"| **Error** | {stats['Error']} | Connection or Parse error |\n")
        f.write(f"| **Total** | {stats['Total']} | |\n\n")
        
        f.write("## 详细列表 (Detailed List)\n\n")
        
        # Group by Category
        results_by_cat = {}
        for r in results:
            cat = r['category']
            if cat not in results_by_cat:
                results_by_cat[cat] = []
            results_by_cat[cat].append(r)
            
        for cat in sorted(results_by_cat.keys()):
            f.write(f"### {cat}\n\n")
            f.write("| Status | Days | Feed | URL | Note |\n")
            f.write("|--------|------|------|-----|------|\n")
            
            # Sort within category: Status priority (Active first), then Days
            def sort_key(x):
                # map status to order
                order = {'Active': 0, 'Recent': 1, 'Stale': 2, 'Inactive': 3, 'No Date Found': 4, 'Error': 5}
                return (order.get(x['status'], 5), x['days_since_update'])
            
            for feed in sorted(results_by_cat[cat], key=sort_key):
                status_icon = {
                    'Active': '✅', 'Recent': '⚠️', 'Stale': '💤', 'Inactive': '💀', 'Error': '❌', 'No Date Found': '❓'
                }.get(feed['status'], '')
                
                days = str(feed['days_since_update']) if feed['days_since_update'] < 9999 else '-'
                note = feed['error'] if feed['error'] else ''
                # Truncate note
                if note and len(note) > 50: note = note[:47] + "..."
                
                f.write(f"| {status_icon} {feed['status']} | {days} | [{feed['title']}]({feed['url']}) | `{feed['url']}` | {note} |\n")
            f.write("\n")

    print(f"Report generated: {REPORT_FILE}")
    print(stats)

if __name__ == '__main__':
    asyncio.run(main())
