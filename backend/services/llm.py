from openai import OpenAI
import json


class DeepSeekService:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    async def filter_titles(self, news_items: list, filter_criteria: str) -> list:
        """
        使用 AI 根据筛选标准过滤新闻标题
        
        Args:
            news_items: 新闻列表,每项包含 {id, title}
            filter_criteria: 筛选标准描述
            
        Returns:
            保留的新闻ID列表
        """
        if not news_items:
            return []
            
        # 构建标题列表
        titles_dict = {item['id']: item['title'] for item in news_items}
        titles_text = "\n".join([f"{id}: {title}" for id, title in titles_dict.items()])
        
        # 构建提示词
        system_prompt = """你是一个专业的新闻筛选助手。根据用户提供的筛选标准,从新闻标题列表中筛选出符合要求的新闻。

返回格式要求:
- 只返回保留新闻的ID列表
- 使用JSON数组格式: [1, 2, 3]
- 不要包含任何解释或额外文字"""

        user_prompt = f"""筛选标准:
{filter_criteria}

新闻标题列表:
{titles_text}

请返回符合筛选标准应该保留的新闻ID列表(JSON数组格式):"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            try:
                kept_ids = json.loads(result_text)
                if isinstance(kept_ids, list):
                    return [int(id) for id in kept_ids if str(id).isdigit()]
            except:
                # 如果JSON解析失败,尝试从文本中提取数字
                import re
                numbers = re.findall(r'\d+', result_text)
                return [int(n) for n in numbers if int(n) in titles_dict]
            
            return []
            
        except Exception as e:
            print(f"AI筛选失败: {e}")
            return []

    async def test_connection(self):
        """测试API连接"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return {"ok": True, "message": "连接成功"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
