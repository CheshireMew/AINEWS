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
        system_prompt = """你是一个专业的新闻价值评估助手。根据用户提供的筛选标准,对每条新闻标题进行价值评分，并打上内容标签。

评分标准：
- 9-10分：极高价值，必读内容（重大创新、独家深度、行业变革）
- 7-8分：高价值内容（有价值的分析、重要资讯、深度报道、综合资讯、项目空投）
- 5-6分：中等价值（一般资讯，有一定参考价值）
- 3-4分：价值较低（浅层信息）
- 1-2分：无价值或负价值（重复内容、纯数据、营销spam、重复）

返回格式要求:
- 必须返回一个JSON数组，数组中包含所有新闻的评估结果
- 每个元素格式: {"id": 新闻ID(整数), "score": 评分(1-10整数), "reason": "评分理由(5字内)", "tag": "内容标签(5字内)"}
- 示例: [{"id": 1, "score": 8, "reason": "技术创新", "tag": "AI技术"}, {"id": 2, "score": 3, "reason": "纯数据", "tag": "市场行情"}]
- tag 字段用于标记新闻的主题类别，如：AI技术、区块链、监管政策、融资、市场分析等
- 直接返回JSON数组，不要任何额外文字"""

        user_prompt = f"""筛选标准:
{filter_criteria}

新闻标题列表:
{titles_text}

请对上述所有新闻打分、标注理由和内容标签，返回JSON数组:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4096  # 增加输出长度限制
            )
            
            result_text = response.choices[0].message.content.strip()
            print(f"[DEBUG] AI Raw Response: {result_text}") # Debug logging
            
            # 尝试解析JSON
            try:
                # 清理可能的markdown代码块标记
                cleaned_text = result_text.strip()
                
                # 移除开头的 ```json 或 ```
                if cleaned_text.startswith("```"):
                    # 找到第一个换行符后的内容
                    lines = cleaned_text.split('\n')
                    # 跳过第一行（```json 或 ```）
                    cleaned_text = '\n'.join(lines[1:])
                
                # 移除结尾的 ```
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3].strip()
                
                # 如果还有尾部不完整的内容，尝试找到最后一个完整的对象
                # 这里简单处理：找到最后一个 }]
                if not cleaned_text.strip().endswith(']'):
                    last_bracket = cleaned_text.rfind(']')
                    if last_bracket > 0:
                        cleaned_text = cleaned_text[:last_bracket+1]
                
                print(f"[DEBUG] Cleaned JSON (first 200 chars): {cleaned_text[:200]}")
                data = json.loads(cleaned_text)
                results = []
                
                if isinstance(data, list):
                    results = data
                    print(f"[DEBUG] Parsed {len(results)} results from array")
                elif isinstance(data, dict):
                     # Extract lists from dict values if any
                     for key, val in data.items():
                         if isinstance(val, list):
                             results = val
                             print(f"[DEBUG] Extracted {len(results)} results from dict key '{key}'")
                             break
                
                if not results:
                    print(f"[WARNING] No results extracted from response. Data type: {type(data)}")
                
                return results

            except Exception as parse_err:
                 print(f"[ERROR] JSON Parse Error: {parse_err}")
                 print(f"[ERROR] Raw text: {result_text[:500]}")
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
