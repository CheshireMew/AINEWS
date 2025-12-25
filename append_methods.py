def archive_to_deduplicated(self, news_ids):
    if not news_ids:
        return 0
    try:
        conn = self.connect()
        cursor = conn.cursor()
        archived_count = 0
        from datetime import datetime
        for news_id in news_ids:
            cursor.execute('SELECT title, content, source_site, source_url, published_at, scraped_at, is_marked_important, site_importance_flag, type FROM news WHERE id = ?', (news_id,))
            row = cursor.fetchone()
            if not row:
                continue
            try:
                cursor.execute('INSERT INTO deduplicated_news (title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, is_marked_important, site_importance_flag, type, original_news_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (row[0], row[1], row[2], row[3], row[4], row[5], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), row[6], row[7], row[8], news_id))
                archived_count += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        conn.close()
        return archived_count
    except:
        return 0

def get_deduplicated_news(self, page=1, limit=50, source=None):
    try:
        conn = self.connect()
        cursor = conn.cursor()
        where_clause = ''
        params = []
        if source:
            where_clause = 'WHERE source_site = ?'
            params.append(source)
        offset = (page - 1) * limit
        query = f'SELECT id, title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, is_marked_important, site_importance_flag, stage, type FROM deduplicated_news {where_clause} ORDER BY deduplicated_at DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        count_query = f'SELECT COUNT(*) FROM deduplicated_news {where_clause}'
        cursor.execute(count_query, params[:-2] if where_clause else [])
        total = cursor.fetchone()[0]
        conn.close()
        return {'data': [dict(row) for row in rows], 'total': total, 'page': page, 'limit': limit}
    except:
        return {'data': [], 'total': 0, 'page': page, 'limit': limit}

def get_deduplicated_stats(self):
    try:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT source_site, COUNT(*) as count FROM deduplicated_news GROUP BY source_site ORDER BY count DESC')
        rows = cursor.fetchall()
        conn.close()
        return [{'source': row[0], 'count': row[1]} for row in rows]
    except:
        return []