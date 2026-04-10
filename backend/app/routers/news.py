from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response, StreamingResponse

from shared.content_contract import (
    CONTENT_KINDS,
    EXPORT_SCOPE_INCOMING,
    PUBLIC_STREAM_MAP,
)
from ..core.exceptions import NotFoundError, ValidationError
from ..core.response import APIResponse
from ..services.content_lifecycle_service import content_lifecycle_service
from ..services.content_service import content_service
from ..services.public_content_service import public_content_service
from .auth import get_current_user

router = APIRouter()


@router.get("/content/overview")
def get_content_overview(kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_service.get_dashboard_overview(kind))


@router.get("/content/stats")
def get_content_stats(kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_service.get_source_stats(kind), message="统计查询成功")


@router.get("/content/incoming")
def get_incoming_content(
    page: int = 1,
    limit: int = 50,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    kind: str = "news",
    user: str = Depends(get_current_user),
):
    data = content_service.list_incoming(page, limit, source, keyword, kind)
    return APIResponse.paginated(data=data["results"], total=data["total"], page=data["page"], limit=data["limit"])


@router.get("/content/source/groups")
def get_source_groups(
    page: int = 1,
    limit: int = 20,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    kind: str = "news",
    user: str = Depends(get_current_user),
):
    return APIResponse.success(data=content_service.list_source_groups(page, limit, source, keyword, kind))


@router.delete("/content/incoming/{entry_id}")
def delete_incoming_content(entry_id: int, user: str = Depends(get_current_user)):
    if not content_lifecycle_service.delete_incoming_entry(entry_id):
        raise NotFoundError("内容不存在")
    return APIResponse.success(message="删除成功")


@router.delete("/content/source/{entry_id}")
def delete_source_content(entry_id: int, user: str = Depends(get_current_user)):
    if not content_lifecycle_service.delete_incoming_entry(entry_id):
        raise NotFoundError("内容不存在")
    return APIResponse.success(message="删除成功")


@router.get("/content/archive")
def get_archive_content(
    page: int = 1,
    limit: int = 50,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    kind: str = "news",
    user: str = Depends(get_current_user),
):
    data = content_service.list_archive(page, limit, source, keyword, kind)
    return APIResponse.paginated(data=data["results"], total=data["total"], page=data["page"], limit=data["limit"])


@router.delete("/content/archive/{entry_id}")
def delete_archive_entry(entry_id: int, user: str = Depends(get_current_user)):
    if not content_lifecycle_service.delete_archive_entry(entry_id):
        raise NotFoundError("内容不存在")
    return APIResponse.success(message="删除成功")


@router.get("/content/blocked")
def get_blocked_content(
    page: int = 1,
    limit: int = 50,
    keyword: Optional[str] = None,
    kind: str = "news",
    user: str = Depends(get_current_user),
):
    data = content_service.list_blocked(page, limit, keyword, kind)
    return APIResponse.paginated(data=data["results"], total=data["total"], page=data["page"], limit=data["limit"])


@router.get("/content/review")
def get_review_queue(
    page: int = 1,
    limit: int = 50,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    kind: str = "news",
    user: str = Depends(get_current_user),
):
    data = content_service.list_review_queue(page, limit, source, keyword, kind)
    return APIResponse.paginated(data=data["results"], total=data["total"], page=data["page"], limit=data["limit"])


@router.get("/content/decisions")
def get_review_decisions(
    decision: str,
    page: int = 1,
    limit: int = 50,
    source: Optional[str] = None,
    keyword: Optional[str] = None,
    kind: str = "news",
    user: str = Depends(get_current_user),
):
    data = content_service.list_review_decisions(decision, page, limit, source, keyword, kind)
    return APIResponse.paginated(data=data["results"], total=data["total"], page=data["page"], limit=data["limit"])


@router.delete("/content/review/{entry_id}")
def delete_review_entry(entry_id: int, user: str = Depends(get_current_user)):
    if not content_lifecycle_service.delete_review_entry(entry_id):
        raise NotFoundError("内容不存在")
    return APIResponse.success(message="删除成功")


@router.post("/content/archive/{entry_id}/restore")
def restore_archive_entry(entry_id: int, user: str = Depends(get_current_user)):
    if not content_lifecycle_service.restore_archive_entry(entry_id):
        raise NotFoundError("内容不存在")
    return APIResponse.success(message="已恢复到采集池")


@router.post("/content/blocked/{entry_id}/restore")
def restore_blocked_entry(entry_id: int, user: str = Depends(get_current_user)):
    if not content_lifecycle_service.restore_blocked_entry(entry_id):
        raise NotFoundError("内容不存在")
    return APIResponse.success(message="已恢复到归档池")


@router.get("/content/export")
def export_content(
    scope: str = EXPORT_SCOPE_INCOMING,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    kind: Optional[str] = None,
    fields: Optional[str] = None,
    user: str = Depends(get_current_user),
):
    payload = content_service.export_content(scope, start_date, end_date, keyword, source, kind, fields)

    def iter_json():
        import json

        yield "["
        for index, item in enumerate(payload):
            if index > 0:
                yield ","
            yield json.dumps(item, default=str, ensure_ascii=False)
        yield "]"

    return StreamingResponse(
        iter_json(),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={content_service.get_export_filename()}"},
    )


@router.get("/public/content")
def get_public_content(stream: str, limit: int = 20, offset: int = 0):
    kind = PUBLIC_STREAM_MAP.get(stream)
    if not kind:
        raise ValidationError("未知公开流类型")
    return APIResponse.success(data=public_content_service.get_public_content(kind, limit, offset))


@router.get("/public/reports")
def get_public_reports(kind: Optional[str] = None, limit: int = 20, offset: int = 0):
    return APIResponse.success(data=public_content_service.get_public_reports(kind, limit, offset))


@router.get("/public/rss.xml")
def get_public_rss(kind: str = "news", limit: int = 20):
    if kind not in CONTENT_KINDS:
        raise ValidationError("未知公开流类型")
    return Response(public_content_service.build_public_rss(kind, limit), media_type="application/rss+xml; charset=utf-8")


@router.get("/public/search")
def search_public_content(query: str, kind: str = "all", limit: int = 20, offset: int = 0):
    if not query or len(query.strip()) < 2:
        raise ValidationError("搜索关键词至少需要2个字符")
    return APIResponse.success(data=public_content_service.search_public_content(query, kind, limit, offset))
