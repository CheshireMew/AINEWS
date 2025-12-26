"""数据库操作基类"""
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Tuple


class DatabaseBase:
    """数据库操作基类，提供通用的CRUD和查询方法"""
    
    @contextmanager
    def get_cursor(self):
        """上下文管理器，自动处理连接、提交和关闭
        
        使用示例:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                return cursor.fetchall()
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict]:
        """执行查询，返回dict列表
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果的dict列表
            
        Example:
            results = self.execute_query(
                "SELECT * FROM news WHERE source_site = ?", 
                ("odaily",)
            )
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_one(self, query: str, params: Tuple = ()) -> Optional[Dict]:
        """执行查询，返回单条记录
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            单条记录的dict，如果没有结果则返回None
            
        Example:
            news = self.execute_one(
                "SELECT * FROM news WHERE id = ?", 
                (123,)
            )
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """执行更新/删除，返回影响行数
        
        Args:
            query: SQL更新/删除语句
            params: 参数
            
        Returns:
            影响的行数
            
        Example:
            rows_affected = self.execute_update(
                "DELETE FROM news WHERE id = ?", 
                (123,)
            )
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        """执行插入，返回lastrowid
        
        Args:
            query: SQL插入语句
            params: 参数
            
        Returns:
            新插入记录的ID
            
        Example:
            new_id = self.execute_insert(
                "INSERT INTO news (title, content) VALUES (?, ?)", 
                ("Title", "Content")
            )
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def paginated_query(
        self, 
        table: str, 
        fields: str = "*",
        where: str = "1=1",
        where_params: Tuple = (),
        order_by: str = "id DESC",
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """通用分页查询
        
        Args:
            table: 表名
            fields: 要查询的字段，默认为"*"
            where: WHERE条件，默认为"1=1"
            where_params: WHERE条件的参数
            order_by: 排序方式，默认为"id DESC"
            page: 页码，从1开始
            limit: 每页数量
            
        Returns:
            包含data、total、page、limit的字典
            
        Example:
            result = self.paginated_query(
                table='news',
                where='source_site = ?',
                where_params=('odaily',),
                order_by='published_at DESC',
                page=1,
                limit=50
            )
            # result = {
            #     'data': [...],
            #     'total': 100,
            #     'page': 1,
            #     'limit': 50
            # }
        """
        offset = (page - 1) * limit
        
        # 查询数据
        query = f"SELECT {fields} FROM {table} WHERE {where} ORDER BY {order_by} LIMIT ? OFFSET ?"
        data = self.execute_query(query, where_params + (limit, offset))
        
        # 查询总数
        count_query = f"SELECT COUNT(*) as total FROM {table} WHERE {where}"
        total_row = self.execute_one(count_query, where_params)
        total = total_row['total'] if total_row else 0
        
        return {
            'data': data,
            'total': total,
            'page': page,
            'limit': limit
        }
