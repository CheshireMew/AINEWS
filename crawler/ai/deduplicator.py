"""AI去重检测器"""
import openai
import yaml
from typing import Dict, List, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class AIDuplicateDetector:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'ai_prompts.yaml'
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化DeepSeek客户端
        self.client = openai.OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url=os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        )
        
        self.model = 'deepseek-chat'
        self.dedup_prompt = self.config['dedup_prompt']
        self.similarity_threshold = float(os.getenv('AI_SIMILARITY_THRESHOLD', '0.85'))
    
    def get_standard_summary(self, news_item: Dict) -> str:
        """使用AI生成标准化摘要用于对比"""
        title = news_item.get('title', '')
        content = news_item.get('content', '')
        text = f"{title} {content}"
        
        prompt = self.dedup_prompt.format(text=text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是文本摘要专家，擅长提取核心事实。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 极低温度保证稳定性
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"生成摘要失败: {e}")
            # fallback：返回标题
            return title
    
    def calculate_similarity(self, summary1: str, summary2: str) -> float:
        """
        计算两个摘要的相似度
        使用Jaccard相似度（简单但有效）
        """
        # 分词（简单按字符分）
        words1 = set(summary1)
        words2 = set(summary2)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_duplicate(self, new_news: Dict, existing_news_list: List[Dict]) -> Dict:
        """
        在已有新闻列表中查找重复
        
        返回: {
            'is_duplicate': bool,
            'duplicate_of': int,  # 新闻ID
            'similarity': float
        }
        """
        if not existing_news_list:
            return {'is_duplicate': False}
        
        # 生成新新闻的标准摘要
        new_summary = self.get_standard_summary(new_news)
        
        best_match = None
        max_similarity = 0.0
        
        for existing in existing_news_list:
            # 生成已有新闻的标准摘要
            existing_summary = self.get_standard_summary(existing)
            
            # 计算相似度
            similarity = self.calculate_similarity(new_summary, existing_summary)
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = existing
        
        # 判断是否重复
        if max_similarity >= self.similarity_threshold:
            return {
                'is_duplicate': True,
                'duplicate_of': best_match.get('id'),
                'similarity': max_similarity,
                'matched_news': best_match
            }
        
        return {
            'is_duplicate': False,
            'similarity': max_similarity
        }
    
    def batch_check_duplicates(self, news_list: List[Dict], existing_news: List[Dict]) -> List[Dict]:
        """批量检测去重"""
        results = []
        for news in news_list:
            result = self.find_duplicate(news, existing_news)
            results.append(result)
        return results


# 测试代码
if __name__ == '__main__':
    detector = AIDuplicateDetector()
    
    # 测试新闻
    news1 = {
        'id': 1,
        'title': 'SEC批准贝莱德比特币现货ETF',
        'content': '美国证券交易委员会批准了贝莱德的比特币现货ETF申请'
    }
    
    news2 = {
        'id': 2,
        'title': '贝莱德BTC ETF获SEC批准',
        'content': '美国SEC今日批准了BlackRock的比特币ETF'
    }
    
    news3 = {
        'id': 3,
        'title': '以太坊完成Dencun升级',
        'content': '以太坊网络成功完成Dencun硬分叉升级'
    }
    
    print("=== AI去重测试 ===\n")
    
    # 测试重复检测
    print("1. 检测news2是否与news1重复:")
    result = detector.find_duplicate(news2, [news1])
    print(f"   是否重复: {result['is_duplicate']}")
    print(f"   相似度: {result.get('similarity', 0):.2%}\n")
    
    print("2. 检测news3是否与news1重复:")
    result = detector.find_duplicate(news3, [news1])
    print(f"   是否重复: {result['is_duplicate']}")
    print(f"   相似度: {result.get('similarity', 0):.2%}\n")
