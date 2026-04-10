from __future__ import annotations

from typing import Iterable

from backend.app.core.config import settings
from shared.content_contract import integration_key
from ..core.exceptions import BusinessError, ValidationError
from ..infrastructure.repositories import repositories
from .telegram_bot import TelegramBot


class TelegramGatewayService:
    @staticmethod
    def _repos():
        return repositories()

    def _resolve_bot_config(self) -> tuple[str | None, str | None]:
        config_repo = self._repos().config
        token = settings.TELEGRAM_BOT_TOKEN or config_repo.get_config(integration_key("telegram", "bot_token"))
        chat_id = settings.TELEGRAM_CHAT_ID or config_repo.get_config(integration_key("telegram", "chat_id"))
        return token, chat_id

    def has_bot_config(self) -> bool:
        token, chat_id = self._resolve_bot_config()
        return bool(token and chat_id)

    def require_bot(self) -> TelegramBot:
        token, chat_id = self._resolve_bot_config()
        if not token or not chat_id:
            raise ValidationError("请先在配置中设置 Telegram Bot Token 和 Chat ID")
        return TelegramBot(token, chat_id)

    async def send_or_raise(self, text: str, error_message: str, parse_mode: str = "HTML") -> None:
        bot = self.require_bot()
        success = await bot.send_message(text, parse_mode=parse_mode)
        if not success:
            raise BusinessError(error_message)

    async def send_many_or_raise(self, messages: Iterable[str], error_message: str, parse_mode: str = "HTML") -> None:
        bot = self.require_bot()
        for message in messages:
            success = await bot.send_message(message, parse_mode=parse_mode)
            if not success:
                raise BusinessError(error_message)

    async def send_test_message(self) -> dict:
        await self.send_or_raise(
            "🔔 <b>AINews Filter</b>\n这是一条测试消息\nThis is a test message.",
            "发送失败，请检查 Bot 配置和网络连接",
        )
        return {"message": "测试消息发送成功"}


telegram_gateway_service = TelegramGatewayService()
