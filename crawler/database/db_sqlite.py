"""SQLite数据库操作类 - 用于开发和测试"""
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from pathlib import Path
import sys

# 添加backend路径以导入core模块
backend_path = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from core.db_base import DatabaseBase

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))
def get_beijing_time():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)
def format_beijing_time(dt):
    """格式化时间为北京时区字符串"""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    # 确保时间带有时区信息
    if dt.tzinfo is None:
        # 假设输入是北京时间
        dt = dt.replace(tzinfo=BEIJING_TZ)
    else:
        # 转换为北京时间
        dt = dt.astimezone(BEIJING_TZ)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

class Database(DatabaseBase):
    def __init__(self, db_path: str = None):
        """初始化SQLite数据库连接"""
        if db_path is None:
            # 默认使用项目目录下的ainews.db
            db_path = str(Path(__file__).parent.parent.parent / 'ainews.db')
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # 让结果可以用字典访问
        # Enable Write-Ahead Logging (WAL) for better concurrency
        try:
            conn.execute('PRAGMA journal_mode=WAL;')
        except:
            pass
            
        cursor = conn.cursor()
        
        # 创建news表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                source_site TEXT NOT NULL,
                source_url TEXT UNIQUE NOT NULL,
                published_at TIMESTAMP NOT NULL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                is_marked_important BOOLEAN DEFAULT FALSE,
                site_importance_flag TEXT,
                
                stage TEXT DEFAULT 'raw',
                keyword_filter_passed BOOLEAN,
                keyword_filter_reason TEXT,
                
                ai_tags TEXT,
                ai_category TEXT,
                ai_score INTEGER,
                ai_summary TEXT,
                
                is_duplicate BOOLEAN DEFAULT FALSE,
                duplicate_of INTEGER,
                
                push_status TEXT DEFAULT 'pending',
                pushed_at TIMESTAMP,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type TEXT DEFAULT 'news'
            )
        ''')
        # 尝试添加 type 字段 (如果不存在)
        try:
            cursor.execute("ALTER TABLE news ADD COLUMN type TEXT DEFAULT 'news'")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        
        # 创建tags表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建news_tags关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_tags (
                news_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (news_id, tag_id),
                FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建processing_logs表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER,
                stage TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建push_logs表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS push_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER,
                platform TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                pushed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
            )
        ''')
        
        # 创建filter_stats表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filter_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_type TEXT NOT NULL,
                rule_pattern TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                last_hit_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建 system_config 表 (User Configs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建deduplicated_news表（存储已去重的原始数据）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deduplicated_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                source_site TEXT NOT NULL,
                source_url TEXT NOT NULL UNIQUE,
                published_at DATETIME NOT NULL,
                scraped_at DATETIME NOT NULL,
                deduplicated_at DATETIME NOT NULL,
                is_marked_important BOOLEAN,
                site_importance_flag TEXT,
                stage TEXT DEFAULT 'deduplicated',
                type TEXT DEFAULT 'news',
                original_news_id INTEGER,
                is_whitelist_restored BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Check and add is_whitelist_restored column if it doesn't exist (Migration)
        try:
            cursor.execute("SELECT is_whitelist_restored FROM deduplicated_news LIMIT 0")
        except sqlite3.OperationalError:
            print("Migrating: Adding is_whitelist_restored column to deduplicated_news")
            cursor.execute("ALTER TABLE deduplicated_news ADD COLUMN is_whitelist_restored BOOLEAN DEFAULT FALSE")
        
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deduplicated_source ON deduplicated_news(source_site)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_deduplicated_time ON deduplicated_news(deduplicated_at)')

        # 创建 curated_news 表（存储经过过滤的精选数据）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curated_news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                source_site TEXT NOT NULL,
                source_url TEXT NOT NULL UNIQUE,
                published_at DATETIME NOT NULL,
                scraped_at DATETIME NOT NULL,
                deduplicated_at DATETIME NOT NULL,
                curated_at DATETIME NOT NULL,
                is_marked_important BOOLEAN,
                site_importance_flag TEXT,
                stage TEXT DEFAULT 'curated',
                type TEXT DEFAULT 'news',
                original_news_id INTEGER,
                ai_status TEXT,
                ai_summary TEXT
            )
        ''')
        
        # Migration: Add ai_status and ai_summary columns if they don't exist
        try:
            cursor.execute("SELECT ai_status FROM curated_news LIMIT 0")
        except sqlite3.OperationalError:
            print("📊 Migrating: Adding ai_status column to curated_news")
            cursor.execute("ALTER TABLE curated_news ADD COLUMN ai_status TEXT")
            
        try:
            cursor.execute("SELECT ai_summary FROM curated_news LIMIT 0")
        except sqlite3.OperationalError:
            print("📊 Migrating: Adding ai_summary column to curated_news")
            cursor.execute("ALTER TABLE curated_news ADD COLUMN ai_summary TEXT")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_curated_source ON curated_news(source_site)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_curated_time ON curated_news(curated_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_curated_ai_status ON curated_news(ai_status)')

        # 黑名单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keyword_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL UNIQUE,
                match_type TEXT DEFAULT 'contains',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 初始化预定义标签
        predefined_tags = [
            ('BTC', 'cryptocurrency'),
            ('ETH', 'cryptocurrency'),
            ('DeFi', 'topic'),
            ('NFT', 'topic'),
            ('Layer2', 'technology'),
            ('监管', 'topic'),
            ('融资', 'event'),
            ('黑客', 'security'),
        ]
        
        try:
            for tag_name, category in predefined_tags:
                cursor.execute(
                    'INSERT OR IGNORE INTO tags (name, category) VALUES (?, ?)',
                    (tag_name, category)
                )
            conn.commit()
        except sqlite3.OperationalError as e:
            # If database is locked, we can skip tag initialization as it's likely already done
            print(f"Skipping tag initialization due to DB lock: {e}")
        finally:
            conn.close()
        
        print(f"✅ SQLite数据库初始化完成 (WAL Mode): {self.db_path}")
    
    def connect(self):
        """创建数据库连接"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn
    
    def insert_news(self, news_data: Dict) -> Optional[int]:
        """插入新闻"""
        conn = None
        try:
            conn = self.connect()
            print(f"[DEBUG] Inserting into DB at: {self.db_path}")
            cursor = conn.cursor()
            
            # Clean content if present (remove excessive newlines)
            if 'content' in news_data and news_data['content']:
                import re
                content = news_data['content']
                # Normalize line endings
                content = content.replace('\r\n', '\n').replace('\r', '\n')
                # Collapse multiple newlines to single newline
                content = re.sub(r'\n\s*\n+', '\n', content)
                # Trim whitespace
                news_data['content'] = content.strip()
            
            # 使用北京时间作为抓取时间
            scraped_at = format_beijing_time(get_beijing_time())
            
            cursor.execute('''
                INSERT INTO news (
                    title, content, source_site, source_url, published_at, scraped_at,
                    is_marked_important, site_importance_flag, stage, type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_data['title'],
                news_data.get('content', ''),
                news_data['source_site'],
                news_data['url'],
                news_data['published_at'],
                scraped_at,  # 显式使用北京时间
                news_data.get('is_marked_important', False),
                news_data.get('site_importance_flag', ''),
                'raw',
                news_data.get('type', 'news')
            ))
            
            news_id = cursor.lastrowid
            conn.commit()
            return news_id
            
        except sqlite3.IntegrityError as e:
            # 详细记录约束冲突原因
            error_msg = str(e)
            print(f"数据库完整性错误: {error_msg}")
            if 'source_url' in error_msg or 'UNIQUE constraint failed: news.source_url' in error_msg:
                print(f"  → URL已存在: {news_data.get('url', 'UNKNOWN')}")
            else:
                print(f"  → 其他约束冲突: {error_msg}")
                print(f"  → 新闻: {news_data.get('title', 'UNKNOWN')[:50]}")
            return None
        except Exception as e:
            print(f"插入新闻失败: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            if conn:
                conn.close()
    
    def update_news(self, news_id: int, updates: Dict):
        """更新新闻"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # 构建UPDATE语句
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [news_id]
            
            cursor.execute(f'''
                UPDATE news SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"更新新闻失败: {e}")
    def delete_news(self, news_id: int) -> bool:
        """删除新闻"""
        conn = None
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"删除新闻失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_deduplicated_news(self, news_id: int) -> bool:
        """删除已去重数据"""
        conn = None
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM deduplicated_news WHERE id = ?", (news_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"删除去重数据失败: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_latest_news_url(self, source_site: str) -> Optional[str]:
        """获取指定来源的最新一条新闻URL"""
        conn = None
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT source_url FROM news 
                WHERE source_site = ? 
                ORDER BY published_at DESC, id DESC 
                LIMIT 1
            ''', (source_site,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"获取最新URL失败: {e}")
            return None
        finally:
            if conn:
                conn.close()
    def get_news_by_time_range(self, hours: int) -> List[Dict]:
        """获取指定时间范围内的新闻"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # 计算时间阈值
            from datetime import datetime, timedelta
            
            # hours=0 表示获取所有新闻
            if hours == 0:
                cursor.execute('''
                    SELECT id, title, content, source_site, source_url, published_at, scraped_at,
                           is_marked_important, site_importance_flag, stage, type
                    FROM news
                    ORDER BY scraped_at DESC
                ''')
            else:
                threshold = datetime.now() - timedelta(hours=hours)
                threshold_str = threshold.strftime('%Y-%m-%d %H:%M:%S')
                
                cursor.execute('''
                    SELECT id, title, content, source_site, source_url, published_at, scraped_at,
                           is_marked_important, site_importance_flag, stage, type
                    FROM news
                    WHERE scraped_at >= ?
                    ORDER BY scraped_at DESC
                ''', (threshold_str,))
            
            
            rows = cursor.fetchall()
            conn.close()
            
            news_list = []
            for row in rows:
                news_list.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'source_site': row[3],
                    'url': row[4],
                    'published_at': row[5],
                    'scraped_at': row[6],
                    'is_marked_important': row[7],
                    'site_importance_flag': row[8],
                    'stage': row[9],
                    'type': row[10]
                })
            
            return news_list
        except Exception as e:
            print(f"获取时间范围新闻失败: {e}")
            return []
    
    def mark_as_duplicate(self, news_id: int, master_id: int, reason: str = ''):
        """标记新闻为重复"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # 更新stage为duplicate，并记录主新闻ID
            cursor.execute('''
                UPDATE news
                SET stage = 'duplicate',
                    is_duplicate = 1,
                    duplicate_of = ?
                WHERE id = ?
            ''', (master_id, news_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"标记重复失败: {e}")
            return False
    
    def get_news_by_stage(self, stage: str, limit: int = 100) -> List[Dict]:
        """按阶段获取新闻"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM news
                WHERE stage = ?
                ORDER BY published_at DESC
                LIMIT ?
            ''', (stage, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"查询新闻失败: {e}")
            return []
    
    def log_processing(self, news_id: int, stage: str, action: str, details: str = None):
        """记录处理日志"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO processing_logs (news_id, stage, action, details)
                VALUES (?, ?, ?, ?)
            ''', (news_id, stage, action, details))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"记录日志失败: {e}")
    
    def insert_or_get_tag(self, tag_name: str, category: str = None) -> int:
        """插入或获取标签ID"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # 尝试获取
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            row = cursor.fetchone()
            
            if row:
                tag_id = row['id']
            else:
                # 插入新标签
                cursor.execute(
                    'INSERT INTO tags (name, category) VALUES (?, ?)',
                    (tag_name, category)
                )
                tag_id = cursor.lastrowid
                conn.commit()
            
            conn.close()
            return tag_id
            
        except Exception as e:
            print(f"插入/获取标签失败: {e}")
            return None
    
    def associate_tags(self, news_id: int, tag_ids: List[int]):
        """关联新闻和标签"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            for tag_id in tag_ids:
                cursor.execute('''
                    INSERT OR IGNORE INTO news_tags (news_id, tag_id)
                    VALUES (?, ?)
                ''', (news_id, tag_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"关联标签失败: {e}")
    
    def archive_to_deduplicated(self, news_ids):
        """将指定的新闻归档到deduplicated_news表"""
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
            print(f'归档了 {archived_count}/{len(news_ids)} 条新闻')
            return archived_count
        except:
            return 0
        
    def get_deduplicated_news(self, page=1, limit=50, source=None, keyword=None):
        """分页查询deduplicated_news表 - 已重构"""
        where = "source_site = ?" if source else "1=1"
        params = [source] if source else []
        
        if keyword:
            where += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.append(term)
            params.append(term)
        
        return self.paginated_query(
            table='deduplicated_news',
            fields='id, title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, is_marked_important, site_importance_flag, stage, type',
            where=where,
            where_params=tuple(params),
            order_by='published_at DESC',
            page=page,
            limit=limit
        )
    
    
    def get_deduplicated_stats(self):
        """获取已去重数据的统计"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT source_site, COUNT(*) as count FROM deduplicated_news GROUP BY source_site ORDER BY count DESC')
            rows = cursor.fetchall()
            conn.close()
            return [{'source': row[0], 'count': row[1]} for row in rows]
        except:
            return []

    # --- Blacklist Methods ---
    def add_blacklist_keyword(self, keyword: str, match_type: str = 'contains') -> bool:
        """添加黑名单关键词"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO keyword_blacklist (keyword, match_type) VALUES (?, ?)', (keyword, match_type))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"添加关键词失败: {e}")
            return False

    def remove_blacklist_keyword(self, id: int) -> bool:
        """删除黑名单关键词"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM keyword_blacklist WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"删除关键词失败: {e}")
            return False

    def get_blacklist_keywords(self):
        """获取所有黑名单关键词"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT id, keyword, match_type, created_at FROM keyword_blacklist ORDER BY created_at DESC')
            rows = cursor.fetchall()
            conn.close()
            return [{'id': r[0], 'keyword': r[1], 'match_type': r[2], 'created_at': r[3]} for r in rows]
        except Exception as e:
            print(f"获取关键词失败: {e}")
            return []

    def filter_news_by_blacklist(self, time_range_hours: int = 24) -> dict:
        """
        根据黑名单过滤新闻
        扫描指定时间范围内 raw 和 deduplicated 状态的新闻
        """
        try:
            keywords = self.get_blacklist_keywords()
            if not keywords:
                return {'scanned': 0, 'filtered': 0}

            from datetime import datetime, timedelta
            # Fix: Use the same format as DB (space separator), ISO format 'T' causes string comparison mismatches
            if time_range_hours <= 0:
                start_time = '1970-01-01 00:00:00'
            else:
                start_time = (datetime.now() - timedelta(hours=time_range_hours)).strftime('%Y-%m-%d %H:%M:%S')
            
            conn = self.connect()
            cursor = conn.cursor()
            
            # 获取待扫描新闻
            # 逻辑变更：只扫描 deduplicated_news 表中 stage='deduplicated' 的项目
            # 原始 news 表的 items 不处理，等待先去重
            
            # 1. 扫描 deduplicated_news
            query = '''
                SELECT id, title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, is_marked_important, site_importance_flag, original_news_id
                FROM deduplicated_news 
                WHERE deduplicated_at >= ? 
                AND stage = 'deduplicated'
                AND (is_whitelist_restored IS NULL OR is_whitelist_restored = 0)
            '''
            
            cursor.execute(query, (start_time,))
            # Set row_factory for dict-like access
            conn.row_factory = sqlite3.Row
            rows = cursor.fetchall()
            
            scanned_count = len(rows)
            filtered_count = 0
            curated_count = 0
            
            for row in rows:
                item_id = row['id']
                title = row['title']
                content = row['content']
                
                # Modified: Filter only checks Title (User Request)
                text_to_check = title.lower()
                
                is_filtered = False
                matched_keyword = None
                
                for kw_item in keywords:
                    kw = kw_item['keyword']
                    match_type = kw_item.get('match_type', 'contains')
                    
                    if match_type == 'regex':
                        import re
                        try:
                            if re.search(kw, text_to_check, re.IGNORECASE):
                                is_filtered = True
                                matched_keyword = f"regex:{kw}"
                                break
                        except re.error:
                            continue
                    else:
                        if kw.lower() in text_to_check:
                            is_filtered = True
                            matched_keyword = kw
                            break
                
                if is_filtered:
                    # Mark as filtered and update timestamp to ensure it appears at top (User Request)
                    current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute("UPDATE deduplicated_news SET stage = 'filtered', deduplicated_at = ? WHERE id = ?", (current_time, item_id))
                    filtered_count += 1
                else:
                    # Clean! Move to curated_news
                    try:
                        cursor.execute('''
                            INSERT INTO curated_news (
                                title, content, source_site, source_url, published_at, scraped_at, 
                                deduplicated_at, curated_at, is_marked_important, site_importance_flag, 
                                stage, type, original_news_id
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'curated', 'news', ?)
                        ''', (
                            row['title'], row['content'], row['source_site'], row['source_url'], 
                            row['published_at'], row['scraped_at'], row['deduplicated_at'], 
                            get_beijing_time().strftime('%Y-%m-%d %H:%M:%S'), 
                            row['is_marked_important'], row['site_importance_flag'], 
                            row['original_news_id']
                        ))
                        
                        # Mark as curated in deduplicated_news so we don't scan again
                        cursor.execute("UPDATE deduplicated_news SET stage = 'curated' WHERE id = ?", (item_id,))
                        curated_count += 1
                    except sqlite3.IntegrityError:
                        # Already exists, just update stage
                        cursor.execute("UPDATE deduplicated_news SET stage = 'curated' WHERE id = ?", (item_id,))
                        pass
                
                # Batch commit every 10 updates to prevent data loss on crash
                if (filtered_count + curated_count) % 10 == 0:
                    conn.commit()

            # 2. Backfill/Retroactive: Scan `curated_news` table for retroactive filtering
            # 当用户添加了新规则后，需要把之前通过但现在命中的“精选新闻”重新拉回“过滤新闻”
            query_curated = '''
                SELECT id, title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, is_marked_important, site_importance_flag, original_news_id
                FROM curated_news
                WHERE curated_at >= ?
            '''
            cursor.execute(query_curated, (start_time,))
            curated_rows = cursor.fetchall()

            retroactive_filtered_count = 0
            
            for row in curated_rows:
                curated_id = row['id']
                title = row['title']
                content = row['content']
                original_news_id = row['original_news_id']
                
                # Modified: Filter only checks Title (User Request)
                text_to_check = title.lower()
                
                is_filtered = False
                matched_keyword = None
                
                for kw_item in keywords:
                    kw = kw_item['keyword']
                    match_type = kw_item.get('match_type', 'contains')
                    
                    if match_type == 'regex':
                        import re
                        try:
                            if re.search(kw, text_to_check, re.IGNORECASE):
                                is_filtered = True
                                matched_keyword = f"regex:{kw}"
                                break
                        except re.error:
                            continue
                    else:
                        if kw.lower() in text_to_check:
                            is_filtered = True
                            matched_keyword = kw
                            break
                            
                if is_filtered:
                    # 命中黑名单！需“回退”操作
                    try:
                        # 1. 从 curated_news 删除
                        cursor.execute("DELETE FROM curated_news WHERE id = ?", (curated_id,))
                        
                        # 2. 找到 deduplicated_news 中的对应记录并更新状态为 filtered
                        # 注意：curated_news 的 id 可能不等于 deduplicated_news 的 id，需要用 original_news_id 或 source_url 关联
                        # 但实际上设计是 curated 来源于 dedup，通常我们存的时候 id 是自增的... 
                        # 这里的 curated_news 是独立表，id 是自增的。我们需要关联回 deduplicated_news。
                        # 在 insert into curated_news 时，应该保存了原始引用。
                        # 查看 insert 语句：发现并没有保存 deduplicated_news 的 id 作为外键，只保存了 original_news_id (news ID)。
                        # 这是一个问题。不过 deduplicated_news 也保存了 original_news_id。
                        # 让我们尝试用 source_url 关联，或者更安全的是：deduplicated_news 表中已经标记为 'curated' 的记录
                        
                        # 在之前的 insert 逻辑中：
                        # INSERT INTO curated_news (... original_news_id) ... VALUES (... row['original_news_id'])
                        # 所以我们可以用 source_url 或 attributes 来匹配。
                        # source_url 是有唯一索引的 (在 dedup 表里没有，但逻辑上应该是唯一的)
                        
                        # Update timestamp to bring to top
                        current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')
                        
                        cursor.execute('''
                            UPDATE deduplicated_news 
                            SET stage = 'filtered', deduplicated_at = ?
                            WHERE source_url = ?
                        ''', (current_time, row['source_url']))
                        
                        retroactive_filtered_count += 1
                        print(f"Retroactive Filter: Removed '{title[:20]}...' from Curated.")
                        
                    except Exception as e:
                        print(f"Retroactive filter error for {curated_id}: {e}")

                # Batch commit
                if (retroactive_filtered_count) % 10 == 0:
                    conn.commit()

            conn.commit()
            conn.close()
            
            total_filtered = filtered_count + retroactive_filtered_count
            print(f"过滤完成: 扫描 {scanned_count} 条新数据, 过滤 {filtered_count} 条; 追溯精选数据过滤 {retroactive_filtered_count} 条")
            return {'scanned': scanned_count, 'filtered': total_filtered, 'retroactive': retroactive_filtered_count}
            
        except Exception as e:
            print(f"执行过滤失败: {e}")
            import traceback
            traceback.print_exc()
            return {'scanned': 0, 'filtered': 0}

    def get_news_for_export(self, start_date=None, end_date=None, 
                              keywords=None, source_site=None, stage=None):
        """获取导出数据 (JSON friendly)"""
        try:
            conn = self.connect()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Switch table based on stage
            table_name = 'news'
            if stage == 'deduplicated':
                table_name = 'deduplicated_news'
            elif stage == 'curated':
                table_name = 'curated_news'
            
            sql = f"SELECT * FROM {table_name} WHERE 1=1"
            params = []
            
            if start_date:
                sql += " AND published_at >= ?"
                params.append(start_date)
            if end_date:
                sql += " AND published_at <= ?"
                params.append(end_date)
            if source_site:
                sql += " AND source_site = ?"
                params.append(source_site)
            # Default to not exporting deleted/filtered unless requested?
            # User wants "Data Management" (Raw) and "Deduplicated".
            if stage:
                sql += " AND stage = ?"
                params.append(stage)
                
            if keywords:
                term = f"%{keywords}%"
                sql += " AND (title LIKE ? OR content LIKE ?)"
                params.append(term)
                params.append(term)
            
            # Default order by published_at DESC
            sql += " ORDER BY published_at DESC"
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            print(f"Export query failed: {e}")
            return []

    def get_curated_news(self, page=1, limit=50, source=None, keyword=None):
        """分页查询 curated_news 表 (精选数据) - 已重构使用基类"""
        # 构建WHERE条件
        where = "source_site = ?" if source else "1=1"
        params = [source] if source else []
        
        if keyword:
            where += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.append(term)
            params.append(term)
        
        # 使用基类的paginated_query方法
        return self.paginated_query(
            table='curated_news',
            fields='id, title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, curated_at, is_marked_important, site_importance_flag, stage, type',
            where=where,
            where_params=tuple(params),
            order_by='published_at DESC',
            page=page,
            limit=limit
        )
    
    def get_filtered_curated_news(self, ai_status, page=1, limit=50):
        """获取经过AI筛选的精选数据 - 已重构"""
        where = "ai_status = ?"
        params = (ai_status,)
        
        return self.paginated_query(
            table='curated_news',
            fields='id, title, content, source_site, source_url, published_at, scraped_at, deduplicated_at, curated_at, is_marked_important, site_importance_flag, stage, type, ai_status, ai_summary',
            where=where,
            where_params=params,
            order_by='published_at DESC',
            page=page,
            limit=limit
        )

    def get_curated_stats(self):
        """获取精选数据统计"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('SELECT source_site, COUNT(*) as count FROM curated_news GROUP BY source_site ORDER BY count DESC')
            rows = cursor.fetchall()
            conn.close()
            return [{'source': row[0], 'count': row[1]} for row in rows]
        except:
            return []

    def delete_curated_news(self, news_id: int) -> bool:
        """删除精选数据（级联删除所有相关数据）"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            # 1. 先获取source_url
            cursor.execute("SELECT source_url FROM curated_news WHERE id = ?", (news_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False
            
            source_url = row['source_url']
            
            # 2. 级联删除：从所有表中删除相同URL的记录
            cursor.execute("DELETE FROM news WHERE source_url = ?", (source_url,))
            deleted_news = cursor.rowcount
            
            cursor.execute("DELETE FROM deduplicated_news WHERE source_url = ?", (source_url,))
            deleted_dedup = cursor.rowcount
            
            cursor.execute("DELETE FROM curated_news WHERE source_url = ?", (source_url,))
            deleted_curated = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"级联删除完成: news({deleted_news}), dedup({deleted_dedup}), curated({deleted_curated})")
            return True
            
        except Exception as e:
            print(f"删除精选数据失败: {e}")
            return False

    def restore_news(self, news_id: int, source_table: str = 'deduplicated_news') -> bool:
        """
        还原被过滤的新闻
        目前只支持从 deduplicated_news 中还原 (stage='filtered' -> 'deduplicated')
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if source_table == 'deduplicated_news' or source_table == 'deduplicated':
                # Restore and whitelist!
                cursor.execute("UPDATE deduplicated_news SET stage = 'deduplicated', is_whitelist_restored = 1 WHERE id = ?", (news_id,))
            elif source_table == 'news':
                cursor.execute("UPDATE news SET stage = 'raw' WHERE id = ?", (news_id,))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"还原数据失败: {e}")
            return False

    def get_latest_news_url(self, source_site: str) -> str:
        """获取指定站点最新抓取的新闻 URL (用于增量抓取)"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            # 优先使用 scraped_at 排序，确保取到最新入库的
            query = "SELECT source_url FROM news WHERE source_site = ? ORDER BY scraped_at DESC LIMIT 1"
            cursor.execute(query, (source_site,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"获取最新URL失败: {e}")
            return None

    def get_recent_news_urls(self, source_site: str, limit: int = 50) -> List[str]:
        """获取指定站点最近抓取的一批新闻 URL (用于更健壮的增量抓取)"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            query = "SELECT source_url FROM news WHERE source_site = ? ORDER BY scraped_at DESC LIMIT ?"
            cursor.execute(query, (source_site, limit))
            rows = cursor.fetchall()
            conn.close()
            return [row[0] for row in rows]
        except Exception as e:
            print(f"获取最近URL列表失败: {e}")
            return []

    def get_filtered_dedup_news(self, page=1, limit=50, keyword=None):
        """获取去重库中的已过滤数据 - 已重构"""
        where = "stage = 'filtered'"
        params = []
        
        if keyword:
            where += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.append(term)
            params.append(term)
        
        return self.paginated_query(
            table='deduplicated_news',
            where=where,
            where_params=tuple(params),
            order_by='published_at DESC',
            page=page,
            limit=limit
        )
        
    def get_filtered_curated_news(self, ai_status, page=1, limit=50, source=None, keyword=None):
        """获取AI筛选后的精选数据 - 已重构"""
        where = "ai_status = ?"
        params = [ai_status]

        if source:
            where += " AND source_site = ?"
            params.append(source)
            
        if keyword:
            where += " AND (title LIKE ? OR content LIKE ?)"
            term = f"%{keyword}%"
            params.append(term)
            params.append(term)
        
        return self.paginated_query(
            table='curated_news',
            where=where,
            where_params=tuple(params),
            order_by='published_at DESC',
            page=page,
            limit=limit
        )
        

    # --- System Config Methods ---
    def get_config(self, key: str) -> Optional[str]:
        """获取系统配置"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Get Config Error ({key}): {e}")
            return None

    def set_config(self, key: str, value: str):
        """设置系统配置"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_config (key, value, updated_at) 
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET 
                    value = excluded.value, 
                    updated_at = excluded.updated_at
            ''', (key, value))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Set Config Error ({key}): {e}")
            return False

    def get_unpushed_curated_news(self) -> List[dict]:
        """获取尚未推送到 Telegram 的精选新闻 (最近 24 小时)"""
        try:
            conn = self.connect()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Select curated news that are NOT in push_logs with status='success'
            query = '''
                SELECT c.* 
                FROM curated_news c
                LEFT JOIN push_logs p ON c.id = p.news_id AND p.status = 'success'
                WHERE p.id IS NULL
                AND c.curated_at >= datetime('now', '-24 hours')
                ORDER BY c.curated_at ASC
            '''
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Get Unpushed News Error: {e}")
            return []
            
    def log_push_status(self, news_id: int, platform: str, status: str, message: str = None):
        """记录推送状态"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO push_logs (news_id, platform, status, message)
                VALUES (?, ?, ?, ?)
            ''', (news_id, platform, status, message))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Log Push Error: {e}")
            return False
