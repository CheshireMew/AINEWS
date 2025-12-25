"""数据库连接和操作模块"""
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Database:
    def __init__(self):
        self.conn_params = {
            'dbname': os.getenv('DB_NAME', 'ainews'),
            'user': os.getenv('DB_USER', 'newsbot'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432')
        }
        self.conn = None
    
    def connect(self):
        """建立数据库连接"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(**self.conn_params, cursor_factory=RealDictCursor)
        return self.conn
    
    def close(self):
        """关闭连接"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def insert_news(self, news_data: Dict) -> int:
        """插入新闻，返回新闻ID"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO news (
                    title, content, source_url, source_site,
                    published_at, is_marked_important, site_importance_flag
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_url) DO NOTHING
                RETURNING id
            """, (
                news_data['title'],
                news_data.get('content', ''),
                news_data['source_url'],
                news_data['source_site'],
                news_data.get('published_at'),
                news_data.get('is_marked_important', False),
                news_data.get('site_importance_flag', '')
            ))
            
            result = cursor.fetchone()
            conn.commit()
            
            if result:
                news_id = result['id']
                self.log_processing(news_id, 'raw', 'scraped', f"从{news_data['source_site']}抓取")
                return news_id
            return None
            
        except Exception as e:
            conn.rollback()
            print(f"插入新闻失败: {e}")
            return None
        finally:
            cursor.close()
    
    def update_news(self, news_id: int, updates: Dict):
        """更新新闻信息"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [news_id]
            
            cursor.execute(f"""
                UPDATE news SET {set_clause} WHERE id = %s
            """, values)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"更新新闻失败: {e}")
        finally:
            cursor.close()
    
    def get_news_by_stage(self, stage: str, limit: int = 100) -> List[Dict]:
        """获取指定阶段的新闻"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM news 
            WHERE processing_stage = %s
            ORDER BY scraped_at DESC
            LIMIT %s
        """, (stage, limit))
        
        result = cursor.fetchall()
        cursor.close()
        return result
    
    def get_recent_news_for_dedup(self, hours: int = 24) -> List[Dict]:
        """获取最近N小时的新闻用于去重"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content FROM news
            WHERE scraped_at >= NOW() - INTERVAL '%s hours'
            AND is_duplicate = FALSE
        """, (hours,))
        
        result = cursor.fetchall()
        cursor.close()
        return result
    
    def log_processing(self, news_id: int, stage: str, action: str, reason: str = '', details: Dict = None):
        """记录处理日志"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO processing_logs (news_id, stage, action, reason, details)
                VALUES (%s, %s, %s, %s, %s)
            """, (news_id, stage, action, reason, psycopg2.extras.Json(details) if details else None))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"记录日志失败: {e}")
        finally:
            cursor.close()
    
    def increment_filter_stat(self, rule_pattern: str, rule_reason: str, rule_type: str):
        """增加过滤规则统计"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO filter_stats (rule_type, rule_pattern, rule_reason, hit_count, last_hit_at)
                VALUES (%s, %s, %s, 1, NOW())
                ON CONFLICT (rule_pattern, date) 
                DO UPDATE SET 
                    hit_count = filter_stats.hit_count + 1,
                    last_hit_at = NOW()
            """, (rule_type, rule_pattern, rule_reason))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"更新统计失败: {e}")
        finally:
            cursor.close()
    
    def insert_or_get_tag(self, tag_name: str, category: str = '') -> int:
        """插入或获取标签ID"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # 先尝试获取
            cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # 不存在则插入
            cursor.execute("""
                INSERT INTO tags (name, category) 
                VALUES (%s, %s) 
                RETURNING id
            """, (tag_name, category))
            
            result = cursor.fetchone()
            conn.commit()
            return result['id']
            
        except Exception as e:
            conn.rollback()
            print(f"插入标签失败: {e}")
            return None
        finally:
            cursor.close()
    
    def link_news_tag(self, news_id: int, tag_id: int, confidence: float):
        """关联新闻和标签"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO news_tags (news_id, tag_id, confidence)
                VALUES (%s, %s, %s)
                ON CONFLICT (news_id, tag_id) DO NOTHING
            """, (news_id, tag_id, confidence))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"关联标签失败: {e}")
        finally:
            cursor.close()
    
    def get_latest_news(self, source_site: str) -> Optional[Dict]:
        """
        获取指定网站的最新一条新闻（用于增量抓取）
        
        Args:
            source_site: 网站名称
            
        Returns:
            新闻字典或None
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, source_url, published_at, scraped_at
                FROM news
                WHERE source_site = %s
                ORDER BY published_at DESC, scraped_at DESC
                LIMIT 1
            ''', (source_site,))
            
            row = cursor.fetchone()
            cursor.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            print(f"获取最新新闻失败: {e}")
            return None

