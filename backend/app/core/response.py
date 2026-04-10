
from datetime import datetime
from typing import Any


class APIResponse:
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = 200):
        return {
            "success": True,
            "data": data,
            "message": message,
            "code": code,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    @staticmethod
    def error(message: str, code: int = 400, error_type: str | None = None, details: Any = None):
        return {
            "success": False,
            "data": None,
            "message": message,
            "code": code,
            "error": {
                "type": error_type or "Error",
                "details": details,
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    @staticmethod
    def paginated(data: list, total: int, page: int, limit: int, message: str = "查询成功"):
        return {
            "success": True,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 0,
            },
            "message": message,
            "code": 200,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
