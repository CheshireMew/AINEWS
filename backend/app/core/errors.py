
from fastapi import Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from logging import getLogger
from .response import APIResponse
from .exceptions import APIException

logger = getLogger("uvicorn")

async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.code,
        content=APIResponse.error(
            message=exc.message,
            code=exc.code,
            error_type=exc.error_type,
            details=getattr(exc, 'details', None)
        ),
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "请求失败"
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse.error(
            message=detail,
            code=exc.status_code,
            error_type="HTTPException",
            details=None if isinstance(exc.detail, str) else exc.detail,
        ),
        headers=exc.headers,
    )

async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIResponse.error(
            message="服务器内部错误",
            code=500,
            error_type="InternalServerError",
            details=str(exc) if logger.level <= 10 else None  # DEBUG模式才显示详情
        )
    )
