from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict

from shared.content_contract import REVIEW_STATUS_DISCARDED, REVIEW_STATUS_SELECTED
from ..core.exceptions import BusinessError, ValidationError
from ..infrastructure.repositories import repositories
from .ai_provider_settings_service import ai_provider_settings_service
from .llm import DeepSeekService


class AIPipelineService:
    @staticmethod
    def _repos():
        return repositories()

    def _build_service(self) -> DeepSeekService:
        config = ai_provider_settings_service.get_config()
        api_key = config["api_key"]
        base_url = config["base_url"]
        model = config["model"]
        if not api_key:
            raise ValidationError("请先配置 DeepSeek API Key")
        return DeepSeekService(api_key, base_url, model)

    async def run_content_review(self, filter_prompt: str, hours: int, content_kind: str = "news") -> Dict:
        service = self._build_service()
        repos = self._repos()
        cutoff_time = "1970-01-01 00:00:00" if hours <= 0 else (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        total_count = repos.review_admin.count_pending_entries(cutoff_time, content_kind)
        if total_count == 0:
            return {"processed": 0, "discarded": 0, "selected": 0, "total": 0, "results": []}

        processed = 0
        discarded = 0
        selected = 0
        results = []

        while True:
            rows = repos.review_admin.get_pending_entries(cutoff_time, content_kind, limit=10)
            if not rows:
                break
            for row in rows:
                processed += 1
                try:
                    decision = await service.review_title(row["title"], filter_prompt, row.get("content", ""))
                except Exception as exc:
                    raise BusinessError(f"AI 审核失败: {exc}") from exc

                review_status = REVIEW_STATUS_SELECTED if decision.get("passed") else REVIEW_STATUS_DISCARDED
                if review_status == REVIEW_STATUS_SELECTED:
                    selected += 1
                else:
                    discarded += 1
                repos.review.save_review_result(
                    row["id"],
                    review_status,
                    decision.get("reason", ""),
                    decision.get("score"),
                    decision.get("category"),
                    decision.get("summary"),
                )
                results.append(
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "review_status": review_status,
                        "score": decision.get("score", 0),
                    }
                )

        return {
            "processed": processed,
            "discarded": discarded,
            "selected": selected,
            "total": total_count,
            "results": results,
        }

    async def test_deepseek_connection(self) -> Dict:
        service = self._build_service()
        result = await service.test_connection()
        if not result["ok"]:
            raise BusinessError(f"连接失败: {result.get('error')}")
        return result


ai_pipeline_service = AIPipelineService()
