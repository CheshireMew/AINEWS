
    def get_curated_news(self, page: int = 1, limit: int = 50, source: Optional[str] = None) -> dict:
        """获取精选数据列表"""
        return self._get_news_common('curated_news', page, limit, source, "stage='curated'")

    def get_curated_stats(self) -> dict:
        """获取精选数据统计"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM curated_news")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT source_site, count(*) FROM curated_news GROUP BY source_site")
            rows = cursor.fetchall()
            conn.close()
            
            return {
                "total": total,
                "by_source": {row[0]: row[1] for row in rows}
            }
        except Exception:
            return {"total": 0, "by_source": {}}

    def delete_curated_news(self, news_id: int) -> bool:
        """删除精选数据"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM curated_news WHERE id = ?", (news_id,))
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"删除精选数据失败: {e}")
            return False

    def restore_news(self, news_id: int, source_table: str = 'deduplicated_news') -> bool:
        """
        还原被过滤的新闻
        目前只支持从 deduplicated_news 中还原 (stage='filtered' -> 'deduplicated')
        因为我们的过滤逻辑主要作用于 deduplicated_news (或 news)
        """
        try:
            conn = self.connect()
            cursor = conn.cursor()
            
            if source_table == 'deduplicated_news':
                # 将 stage 从 filtered 改回 deduplicated
                # 这样下一次过滤扫描时，它会被再次检查（除非加入白名单，否则可能再次被过滤）
                # 为了防止立即被过滤，用户可能需要先修改黑名单
                cursor.execute("UPDATE deduplicated_news SET stage = 'deduplicated' WHERE id = ?", (news_id,))
            elif source_table == 'news':
                cursor.execute("UPDATE news SET stage = 'raw' WHERE id = ?", (news_id,))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"还原数据失败: {e}")
            return False
