from __future__ import annotations

import json
from typing import Any, Dict

from openai import AsyncOpenAI


class DeepSeekService:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def _parse_json(self, content: str) -> Dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3].strip()
        return json.loads(text)

    async def review_title(self, title: str, review_prompt: str, content: str = "") -> Dict[str, Any]:
        system_prompt = """
你是新闻审核助手。请基于用户给出的偏好判断内容是否应该进入精选输出。

只返回 JSON 对象，字段如下：
{
  "passed": true,
  "score": 8,
  "reason": "一句中文短理由",
  "category": "一句中文分类",
  "summary": "一句中文摘要"
}

要求：
1. score 为 1-10 的整数
2. passed 为 true 表示应保留，为 false 表示应丢弃
3. 不要输出任何 JSON 之外的内容
"""
        user_prompt = f"""审核偏好：
{review_prompt}

标题：
{title}

正文摘要：
{content[:1200]}
"""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        raw = response.choices[0].message.content or "{}"
        parsed = self._parse_json(raw)
        return {
            "passed": bool(parsed.get("passed", False)),
            "score": int(parsed.get("score", 0) or 0),
            "reason": str(parsed.get("reason", "") or ""),
            "category": str(parsed.get("category", "") or ""),
            "summary": str(parsed.get("summary", "") or ""),
        }

    async def test_connection(self):
        try:
            await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hello"}],
                max_tokens=8,
            )
            return {"ok": True, "message": "连接成功"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
