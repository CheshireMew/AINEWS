"""统一异常处理"""


class APIException(Exception):
    """API基础异常"""
    
    def __init__(self, message: str, code: int = 400, error_type: str = None):
        self.message = message
        self.code = code
        self.error_type = error_type or self.__class__.__name__
        super().__init__(self.message)


class ValidationError(APIException):
    """参数验证错误"""
    
    def __init__(self, message: str, details: dict = None):
        self.details = details
        super().__init__(message, code=400, error_type="ValidationError")


class NotFoundError(APIException):
    """资源不存在"""
    
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, code=404, error_type="NotFoundError")


class DatabaseError(APIException):
    """数据库错误"""
    
    def __init__(self, message: str):
        super().__init__(message, code=500, error_type="DatabaseError")


class AuthenticationError(APIException):
    """认证错误"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, code=401, error_type="AuthenticationError")


class PermissionError(APIException):
    """权限错误"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, code=403, error_type="PermissionError")


class BusinessError(APIException):
    """业务逻辑错误"""
    
    def __init__(self, message: str):
        super().__init__(message, code=400, error_type="BusinessError")
