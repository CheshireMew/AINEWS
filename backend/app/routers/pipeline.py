from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..core.response import APIResponse
from .auth import get_current_user
from ..services.ai_pipeline_service import ai_pipeline_service
from ..services.content_admin_service import content_admin_service
from ..services.content_lifecycle_service import content_lifecycle_service
from ..services.deduplication_service import deduplication_service
from ..services.scraper_command_service import scraper_command_service
from ..services.scraper_runtime_state_service import scraper_runtime_state_service
from ..services.telegram_delivery_service import telegram_delivery_service

router = APIRouter()


class RunScraperRequest(BaseModel):
    items: int = 10


class ConfigRequest(BaseModel):
    interval: Optional[str] = None
    limit: Optional[int] = None


class ArchiveBuildRequest(BaseModel):
    time_window_hours: int = 24
    action: str = "mark"
    threshold: float = 0.50
    kind: str = "news"


class CheckSimilarityRequest(BaseModel):
    news_id_1: int
    news_id_2: int


class ReviewRunRequest(BaseModel):
    hours: int = 8
    filter_prompt: str
    kind: str = "news"


class AddBlacklistRequest(BaseModel):
    keyword: str
    match_type: str = "contains"
    kind: str = "news"


class BlocklistRunRequest(BaseModel):
    time_range_hours: int = 24
    kind: str = "news"


class TelegramSendRequest(BaseModel):
    news_ids: List[int]


class ApiKeyCreate(BaseModel):
    key_name: str
    notes: Optional[str] = None


@router.post("/spiders/run/{name}")
async def run_spider(name: str, req: RunScraperRequest, user: str = Depends(get_current_user)):
    return await scraper_command_service.request_run(name, req.items)


@router.post("/spiders/stop/{name}")
async def stop_scraper(name: str, user: str = Depends(get_current_user)):
    return await scraper_command_service.request_stop(name)


@router.get("/spiders")
def get_spiders(user: str = Depends(get_current_user)):
    return scraper_runtime_state_service.get_spiders()


@router.get("/spiders/status")
def get_spider_status(user: str = Depends(get_current_user)):
    return scraper_runtime_state_service.get_spider_status()


@router.post("/spiders/config/{name}")
def config_scraper(name: str, req: ConfigRequest, user: str = Depends(get_current_user)):
    return scraper_runtime_state_service.update_scraper_config(name, req.interval, req.limit)


@router.post("/content/archive/build")
async def build_archive(req: ArchiveBuildRequest, user: str = Depends(get_current_user)):
    return await deduplication_service.deduplicate_news(req.time_window_hours, req.action, req.threshold, req.kind)


@router.post("/content/archive/check_similarity")
async def check_news_similarity(req: CheckSimilarityRequest, user: str = Depends(get_current_user)):
    return await deduplication_service.check_news_similarity(req.news_id_1, req.news_id_2)


@router.post("/delivery/daily/news")
async def trigger_daily_push(user: str = Depends(get_current_user)):
    return await telegram_delivery_service.auto_daily_best_push(force=True)


@router.post("/delivery/daily/article")
async def trigger_daily_article_push(user: str = Depends(get_current_user)):
    return await telegram_delivery_service.auto_daily_article_push(force=True)


@router.post("/delivery/test")
async def test_telegram_push(user: str = Depends(get_current_user)):
    result = await telegram_delivery_service.test_telegram_push()
    return APIResponse.success(message=result["message"])


@router.post("/delivery/send")
async def send_news_to_telegram(request: TelegramSendRequest, user: str = Depends(get_current_user)):
    result = await telegram_delivery_service.send_news_to_telegram(request.news_ids)
    return APIResponse.success(message=f"成功发送 {result['sent_count']} 条内容到 Telegram", data=result)


@router.get("/content/blocklist")
def get_blacklist(kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_admin_service.get_blacklist(kind))


@router.post("/content/blocklist")
def add_blacklist(req: AddBlacklistRequest, user: str = Depends(get_current_user)):
    return APIResponse.success(message=content_admin_service.add_blacklist(req.keyword, req.match_type, req.kind)["message"])


@router.delete("/content/blocklist/{entry_id}")
def delete_blacklist(entry_id: int, user: str = Depends(get_current_user)):
    return APIResponse.success(message=content_admin_service.delete_blacklist(entry_id)["message"])


@router.post("/content/blocked/apply")
def filter_news(req: BlocklistRunRequest, user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_lifecycle_service.apply_blocklist(req.time_range_hours, req.kind))


@router.post("/content/review/run")
async def run_content_review(req: ReviewRunRequest, user: str = Depends(get_current_user)):
    return APIResponse.success(data=await content_lifecycle_service.run_review(req.filter_prompt, req.hours, req.kind))


@router.post("/content/review/{entry_id}/requeue")
def reset_review_item(entry_id: int, user: str = Depends(get_current_user)):
    return APIResponse.success(message=content_lifecycle_service.reset_review_item(entry_id)["message"])


@router.post("/content/review/requeue")
def reset_review_queue(kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_lifecycle_service.reset_review_queue(kind))


@router.post("/content/review/clear")
def clear_review_results(kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_lifecycle_service.clear_review_results(kind))


@router.post("/content/blocked/restore")
def restore_blocked_queue(kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_lifecycle_service.restore_blocked_queue(kind))


@router.post("/integration/analyst/keys")
async def create_api_key(request: ApiKeyCreate, user: str = Depends(get_current_user)):
    result = await content_admin_service.create_analyst_api_key(request.key_name, request.notes)
    return APIResponse.success(message=result["message"], data=result)


@router.get("/integration/analyst/keys")
def get_analyst_api_keys(user: str = Depends(get_current_user)):
    return APIResponse.success(data=content_admin_service.get_analyst_api_keys())


@router.delete("/integration/analyst/keys/{key_id}")
async def delete_api_key(key_id: int, user: str = Depends(get_current_user)):
    result = await content_admin_service.delete_analyst_api_key(key_id)
    return APIResponse.success(message=result["message"])


@router.post("/integration/ai/test")
async def test_deepseek_connection(user: str = Depends(get_current_user)):
    return APIResponse.success(data=await ai_pipeline_service.test_deepseek_connection())
