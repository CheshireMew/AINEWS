from typing import List, Optional

from .base_repository import BaseRepository


class ProcessingRepository(BaseRepository):
    def log_processing(self, news_id: int, stage: str, action: str, details: Optional[str] = None):
        try:
            self.execute(
                'INSERT INTO processing_logs (news_id, stage, action, details) VALUES (?, ?, ?, ?)',
                (news_id, stage, action, details),
            )
        except Exception as e:
            print(f"记录日志失败: {e}")

    def link_news_tag(self, news_id: int, tag_id: int, confidence: float = 0.9):
        try:
            self.execute(
                'INSERT OR IGNORE INTO news_tags (news_id, tag_id) VALUES (?, ?)',
                (news_id, tag_id),
            )
        except Exception as e:
            print(f"关联标签失败: {e}")
