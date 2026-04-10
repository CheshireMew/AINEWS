from typing import List, Optional

from .base_repository import BaseRepository


class TagRepository(BaseRepository):
    def insert_or_get_tag(self, tag_name: str, category: Optional[str] = None) -> Optional[int]:
        try:
            cursor = self.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            row = cursor.fetchone()
            if row:
                return row['id']

            cursor = self.execute('INSERT INTO tags (name, category) VALUES (?, ?)', (tag_name, category))
            return cursor.lastrowid
        except Exception as e:
            print(f"插入/获取标签失败: {e}")
            return None

    def associate_tags(self, news_id: int, tag_ids: List[int]):
        try:
            for tag_id in tag_ids:
                self.execute(
                    'INSERT OR IGNORE INTO news_tags (news_id, tag_id) VALUES (?, ?)',
                    (news_id, tag_id),
                )
        except Exception as e:
            print(f"关联标签失败: {e}")
