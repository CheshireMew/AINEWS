from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..core.response import APIResponse
from ..services.ai_provider_settings_service import ai_provider_settings_service
from ..services.automation_settings_service import automation_settings_service
from ..services.delivery_settings_service import delivery_settings_service
from ..services.review_settings_service import review_settings_service
from ..services.rss_source_service import rss_source_service
from ..services.system_settings_service import system_settings_service
from ..services.telegram_settings_service import telegram_settings_service
from .auth import get_current_user

router = APIRouter()


class SystemTimezoneConfig(BaseModel):
    timezone: str


class DeliveryScheduleConfig(BaseModel):
    news_time: str | None = None
    article_time: str | None = None


class AutomationWindowConfig(BaseModel):
    dedup_hours: int | None = Field(default=None, ge=1, le=720)
    dedup_window_hours: int | None = Field(default=None, ge=1, le=720)
    filter_hours: int | None = Field(default=None, ge=1, le=720)
    ai_scoring_hours: int | None = Field(default=None, ge=1, le=720)
    push_hours: int | None = Field(default=None, ge=1, le=720)


class AutomationConfigRequest(BaseModel):
    news: AutomationWindowConfig | None = None
    article: AutomationWindowConfig | None = None


class TelegramConfigRequest(BaseModel):
    bot_token: str
    chat_id: str
    enabled: bool = False


class AIProviderConfigRequest(BaseModel):
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"


class AIReviewConfigRequest(BaseModel):
    prompt: str | None = None
    hours: int | None = Field(default=8, ge=1, le=720)


class RssSourceRequest(BaseModel):
    slug: str | None = None
    display_name: str
    feed_url: str
    site_url: str
    content_kind: str = "article"
    parser_type: str = "generic"
    default_limit: int = Field(default=20, ge=1, le=100)
    default_interval: int = Field(default=240, ge=5, le=10080)
    enabled: bool = True


@router.get("/system/timezone")
def get_system_timezone(user: str = Depends(get_current_user)):
    return APIResponse.success(data=system_settings_service.get_timezone())


@router.post("/system/timezone")
def set_system_timezone(config: SystemTimezoneConfig, user: str = Depends(get_current_user)):
    result = system_settings_service.set_timezone(config.timezone)
    return APIResponse.success(message=result["message"])


@router.get("/delivery/schedule")
def get_delivery_schedule(user: str = Depends(get_current_user)):
    return APIResponse.success(data=delivery_settings_service.get_schedule())


@router.post("/delivery/schedule")
def set_delivery_schedule(config: DeliveryScheduleConfig, user: str = Depends(get_current_user)):
    result = delivery_settings_service.set_schedule(config.news_time, config.article_time)
    return APIResponse.success(message=result["message"])


@router.get("/config/automation")
def get_automation_config(user: str = Depends(get_current_user)):
    return APIResponse.success(data=automation_settings_service.get_config())


@router.post("/config/automation")
def set_automation_config(req: AutomationConfigRequest, user: str = Depends(get_current_user)):
    result = automation_settings_service.set_config(req.model_dump())
    return APIResponse.success(message=result["message"])


@router.get("/integration/telegram")
def get_telegram_config(user: str = Depends(get_current_user)):
    return APIResponse.success(data=telegram_settings_service.get_config())


@router.post("/integration/telegram")
def set_telegram_config(config: TelegramConfigRequest, user: str = Depends(get_current_user)):
    return APIResponse.success(message=telegram_settings_service.set_config(config.model_dump())["message"])


@router.get("/integration/ai")
def get_ai_provider_config(user: str = Depends(get_current_user)):
    return APIResponse.success(data=ai_provider_settings_service.get_config())


@router.post("/integration/ai")
def set_ai_provider_config(config: AIProviderConfigRequest, user: str = Depends(get_current_user)):
    return APIResponse.success(message=ai_provider_settings_service.set_config(config.model_dump())["message"])


@router.get("/review/settings")
def get_ai_review_config(kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(data=review_settings_service.get_config(kind))


@router.post("/review/settings")
def set_ai_review_config(config: AIReviewConfigRequest, kind: str = "news", user: str = Depends(get_current_user)):
    return APIResponse.success(message=review_settings_service.set_config(config.prompt, config.hours, kind)["message"])


@router.get("/rss/sources")
def get_rss_sources(user: str = Depends(get_current_user)):
    return APIResponse.success(data=rss_source_service.list_sources())


@router.post("/rss/sources")
def create_rss_source(config: RssSourceRequest, user: str = Depends(get_current_user)):
    return APIResponse.success(message="RSS 源已创建", data=rss_source_service.create_source(config.model_dump()))


@router.put("/rss/sources/{source_id}")
def update_rss_source(source_id: int, config: RssSourceRequest, user: str = Depends(get_current_user)):
    return APIResponse.success(message="RSS 源已更新", data=rss_source_service.update_source(source_id, config.model_dump()))


@router.delete("/rss/sources/{source_id}")
def delete_rss_source(source_id: int, user: str = Depends(get_current_user)):
    return APIResponse.success(message=rss_source_service.delete_source(source_id)["message"])
