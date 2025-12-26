"""统一API响应格式"""
from typing import Any, Optional
from datetime import datetime


class APIResponse:
    """API响应包装器"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = 200):
        """成功响应
        
        Args:
            data: 返回的数据
            message: 响应消息
            code: HTTP状态码
            
        Returns:
            标准化的成功响应
        """
        return {
            "success": True,
            "data": data,
            "message": message,
            "code": code,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @staticmethod
    def error(
        message: str, 
        code: int = 400, 
        error_type: str = None, 
        details: Any = None
    ):
        """错误响应
        
        Args:
            message: 错误消息
            code: HTTP状态码
            error_type: 错误类型
            details: 错误详情
            
        Returns:
            标准化的错误响应
        """
        return {
            "success": False,
            "data": None,
            "message": message,
            "code": code,
            "error": {
                "type": error_type or "Error",
                "details": details
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @staticmethod
    def paginated(
        data: list, 
        total: int, 
        page: int, 
        limit: int, 
        message: str = "查询成功"
    ):
        """分页响应
        
        Args:
            data: 数据列表
            total: 总记录数
            page: 当前页码
            limit: 每页数量
            message: 响应消息
            
        Returns:
            标准化的分页响应
        """
        return {
            "success": True,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 0
            },
            "message": message,
            "code": 200,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
