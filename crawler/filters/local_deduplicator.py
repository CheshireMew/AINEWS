"""本地去重模块 - 在AI处理前快速识别重复新闻"""
import re
import json
import os
from typing import List, Set, Tuple
from difflib import SequenceMatcher
from datetime import datetime, timedelta
import logging

try:
    import jieba
    # Initialize jieba and add custom words
    jieba.setLogLevel(logging.ERROR)
    jieba.add_word('币安')
    jieba.add_word('CZ')
    jieba.add_word('Aave')
    jieba.add_word('Polymarket')
except ImportError:
    jieba = None

class LocalDeduplicator:
    """
    本地新闻去重器
    
    策略：
    1. 提取关键数字和关键词
    2. 计算标题相似度
    3. 在时间窗口内查找重复
    """
    
    def __init__(self, similarity_threshold: float = 0.55, time_window_hours: int = 24):
        """
        Args:
            similarity_threshold: 相似度阈值 (0-1)，超过此值认为是重复（默认0.55）
            time_window_hours: 时间窗口（小时），只在此窗口内比较
        """
        self.similarity_threshold = similarity_threshold
        self.time_window_hours = time_window_hours
        
        # 加载同义词字典
        self.synonyms = {}
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'synonyms.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.synonyms = json.load(f)
        except Exception as e:
            print(f"Error loading synonyms: {e}")

        # Add dictionary words to Jieba from synonyms keys (if they are words)
        if jieba:
            for k, v in self.synonyms.items():
                if v and len(k) > 1 and k.isalnum(): # Add Key (e.g. Binance)
                     jieba.add_word(k)
                if v and len(v) > 1 and v.isalnum() and not v.isascii(): # Add Value (e.g. 币安)
                     jieba.add_word(v)
            # Add specific known words just in case
            jieba.add_word('币安')
            jieba.add_word('CZ')
            jieba.add_word('Aave')
            jieba.add_word('Polymarket')
    
    def extract_key_features(self, title: str) -> dict:
        """
        提取标题的关键特征
        
        Returns:
            {
                'numbers': set of standardized numbers,  # 标准化后的数字集合
                'keywords': set of keywords,             # 关键词集合
                'normalized': str                        # 标准化后的标题
            }
        """
        # 标准化数字：将"万"、"亿"等单位转换为实际数值
        def normalize_number(text):
            """将中文数字单位转换为标准形式"""
            # 预处理中文数字词
            replacements = {
                '千万': '1000万',
                '百万': '100万',
                '十万': '10万',
                '数千万': '1000万', # 模糊处理
                '数百万': '100万',
                '数万': '1万'
            }
            norm_text = text
            for k, v in replacements.items():
                norm_text = norm_text.replace(k, v)
                
            # 匹配 "4.6 万" "46,379" "1.37亿" 等格式
            patterns = [
                (r'(\d+\.?\d*)\s*万', lambda m: str(float(m.group(1)) * 10000)),
                (r'(\d+\.?\d*)\s*亿', lambda m: str(float(m.group(1)) * 100000000)),
                (r'(\d{1,3}(,\d{3})+)', lambda m: m.group(1).replace(',', ''))  # 移除千位分隔符
            ]
            
            result = norm_text
            for pattern, repl in patterns:
                result = re.sub(pattern, repl, result)
            return result
        
        def normalize_synonyms(text):
            """同义词归一化"""
            # 使用 self.synonyms
            synonyms = self.synonyms
            
            # Case insensitive replacement for English keys
            res = text
            for k, v in synonyms.items():
                if not k: continue
                if k.isascii():
                    pattern = re.compile(re.escape(k), re.IGNORECASE)
                    res = pattern.sub(v, res)
                else:
                    res = res.replace(k, v)
            return res

        # 先标准化数字
        normalized_title = normalize_number(title)
        
        # 同义词归一化 (用于分词前，提高关键词一致性)
        normalized_title = normalize_synonyms(normalized_title)
        
        # 提取所有数字（整数和小数）
        numbers = set(re.findall(r'\d+\.?\d*', normalized_title))
        # 过滤掉太小的数字（可能是年份、日期等）
        numbers = {n for n in numbers if float(n) >= 100 or '.' in n}
        
        # 提取关键词（人名、机构名、币种等）
        # 移除常见的连接词和标点
        # Expanded stop words for better precision
        stop_words = {'的', '了', '在', '和', '与', '及', '等', '等等', '今日', '昨日', 
                     '价值', '约', '枚', '美元', '亿', '万', '增持', '减持', '今天', '昨天',
                     '旗下', '合', '被', '因', '且', '或', '将', '向', '至', '疑似', '指控', '旨在', '增强',
                     '已', '应', '该', '对', '对于', '把', '给', '让', '从', '到', '处', '于', '关于', '将会'}
        
        # 使用 jieba 分词
        try:
            import jieba
            # jieba.cut_for_search 适合搜索引擎模式，粒度较细
            words = set(jieba.cut_for_search(normalized_title))
        except ImportError:
            # Fallback if jieba not available (though we installed it)
            english_words = set(re.findall(r'[A-Za-z]+', title))
            chinese_parts = re.split(r'[，。、：；！？\s]+', title)
            chinese_words = set()
            for part in chinese_parts:
                chinese_only = re.sub(r'[A-Za-z0-9\s\.,]+', '', part)
                if len(chinese_only) >= 2:
                    chinese_words.add(chinese_only)
            words = english_words | chinese_words

        # 过滤停用词和标点
        keywords = {w for w in words if w not in stop_words and len(w.strip()) > 1} # Keep words > 1 char
        
        # 标准化：去除空格、标点、统一大小写、标准化数字
        normalized = re.sub(r'[，。、：；！？\s\-—_,]+', '', normalized_title.lower())
        
        return {
            'numbers': numbers,
            'keywords': keywords,
            'normalized': normalized
        }
    
    
    def _numbers_are_close(self, n1_str, n2_str):
        """
        判断两个数字是否应该被认为相同
        
        策略：比较前导数字（有效数字的前2-3位）
        例如：
        - 46000 vs 46379 → 都是"46"开头 → 相同
        - 1370000000 vs 1300000000 → 都是"13"开头 → 相同
        - 5000000 vs 4800000 → "50" vs "48" → 相同（±5%兜底）
        """
        try:
            n1, n2 = float(n1_str), float(n2_str)
            
            if n1 == n2:
                return True
            if n1 == 0 or n2 == 0:
                return False
            
            # 提取有效数字的前导部分
            def get_leading_digits(num, precision=2):
                """获取数字的前导有效数字"""
                import math
                if num == 0:
                    return "0"
                # 获取数量级
                magnitude = int(math.floor(math.log10(abs(num))))
                # 标准化到[1, 10)区间
                normalized = num / (10 ** magnitude)
                # 取前precision位
                leading = int(normalized * (10 ** (precision - 1)))
                return str(leading)
            
            leading1 = get_leading_digits(n1, precision=2)
            leading2 = get_leading_digits(n2, precision=2)
            
            # 如果前导数字相同，认为是同一个数字
            if leading1 == leading2:
                return True
            
            # 兜底：如果前导不同，再用相对误差判断（容差10%）
            diff = abs(n1 - n2) / max(n1, n2)
            return diff <= 0.10
            
        except:
            return n1_str == n2_str

    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        计算两个标题的相似度
        
        使用组合策略：
        0. 字串包含检测 (如果完全包含且不冲突，直接高分)
        1. 关键数字近似匹配 - 如果关键数字接近（±5%误差），相似度+0.4
        2. 关键词匹配度 (50%)
        3. 字符串序列相似度 (20%)
        
        Returns:
            相似度分数 (0-1)
        """
        features1 = self.extract_key_features(title1)
        features2 = self.extract_key_features(title2)
        
        # 0. 包含关系检查（快速通道）
        # 针对 "Metaplanet董事会批准增持比特币计划" vs "Metaplanet董事会批准增持比特币计划，拟..."
        norm1 = features1['normalized']
        norm2 = features2['normalized']
        
        if norm1 and norm2 and (norm1 in norm2 or norm2 in norm1):
            len1, len2 = len(norm1), len(norm2)
            ratio = min(len1, len2) / max(len1, len2)
            
            # 如果包含且长度比例合理（避免单个字匹配，如 "BTC" in "BTC大跌..."）
            # 长度比至少0.25 (即短标题至少是长标题的1/4长度)
            if ratio > 0.25:
                # 检查数字冲突：如果在包含的情况下，短标题的数字与长标题的不一致，则不能判定为重复
                nums1, nums2 = features1['numbers'], features2['numbers']
                
                # 定义冲突检查
                def has_number_conflict(short_nums, long_nums):
                    if not short_nums: return False # 短标题无数字，视为概括性标题，不冲突
                    # 短标题有数字，必须在长标题中找到（允许近似）
                    if not long_nums: return True # 短有长无，必定冲突（不应该发生，因为是包含关系，除非包含检测只基于去数字后的文本）
                    
                    found_all = True
                    for n_short in short_nums:
                        found_one = False
                        for n_long in long_nums:
                            if self._numbers_are_close(n_short, n_long):
                                found_one = True
                                break
                        if not found_one:
                            found_all = False
                            break
                    return not found_all
                
                # 确定长短
                if len(norm1) < len(norm2):
                    conflict = has_number_conflict(nums1, nums2)
                else:
                    conflict = has_number_conflict(nums2, nums1)
                
                if not conflict:
                    return 0.95  # 极高相似度
        
        # 1. 字符串序列相似度（降低权重）
        seq_sim = SequenceMatcher(None, features1['normalized'], features2['normalized']).ratio()
        
        # 2. 数字匹配度（提高权重，并支持近似匹配）
        nums1, nums2 = features1['numbers'], features2['numbers']
        
        if nums1 and nums2:
            # 计算精确匹配数量
            exact_matches = len(nums1 & nums2)
            
            # 计算近似匹配数量（前导数字匹配）
            approx_matches = 0
            for n1 in nums1:
                for n2 in nums2:
                    if n1 not in nums2 and n2 not in nums1:  # 不是精确匹配
                        if self._numbers_are_close(n1, n2):
                            approx_matches += 1
                            break  # 每个数字最多匹配一次
            
            total_matches = exact_matches + approx_matches
            total_numbers = len(nums1 | nums2)
            
            # Jaccard相似度
            num_sim = total_matches / total_numbers if total_numbers > 0 else 0
            
            # 如果主要数字都匹配（精确或近似），给予高分
            if total_matches >= 2:  # 至少2个关键数字匹配
                num_bonus = 0.5  # 提高奖励分数
            elif total_matches >= 1:  # 至少1个关键数字匹配
                num_bonus = 0.3
            else:
                num_bonus = 0
        elif not nums1 and not nums2:
            num_sim = 1.0
            num_bonus = 0
        else:
            num_sim = 0
            num_bonus = 0
        
        # 3. 关键词匹配度（提高权重）
        kw1, kw2 = features1['keywords'], features2['keywords']
        if kw1 and kw2:
            kw_sim = len(kw1 & kw2) / len(kw1 | kw2)
        elif not kw1 and not kw2:
            kw_sim = seq_sim
        else:
            kw_sim = 0
        
        # 加权计算：数字和关键词权重提高
        base_similarity = seq_sim * 0.15 + num_sim * 0.25 + kw_sim * 0.6
        
        # 加上数字匹配奖励
        final_similarity = min(1.0, base_similarity + num_bonus)
        
        return final_similarity
    
    def find_duplicates(self, news_list: List[dict]) -> List[Tuple[int, int, float]]:
        """
        在新闻列表中找出所有重复对
        
        Args:
            news_list: 新闻列表，每条新闻需包含 title, published_at
        
        Returns:
            [(index1, index2, similarity), ...] 重复对列表
        """
        duplicates = []
        n = len(news_list)
        
        for i in range(n):
            for j in range(i + 1, n):
                news1 = news_list[i]
                news2 = news_list[j]
                
                # 检查时间窗口
                try:
                    time1 = news1['published_at']
                    time2 = news2['published_at']
                    
                    if isinstance(time1, str):
                        time1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
                    if isinstance(time2, str):
                        time2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
                    
                    time_diff = abs((time1 - time2).total_seconds() / 3600)
                    
                    # 超出时间窗口，不比较
                    if time_diff > self.time_window_hours:
                        continue
                        
                except Exception:
                    # 时间解析失败，继续比较
                    pass
                
                # 计算相似度
                similarity = self.calculate_similarity(news1['title'], news2['title'])
                
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, similarity))
        
        return duplicates
    
    def mark_duplicates(self, news_list: List[dict]) -> List[dict]:
        """
        标记新闻列表中的重复项
        
        策略：在每组重复中，保留最早的一条，标记其他为重复
        
        Args:
            news_list: 新闻列表
        
        Returns:
            标记后的新闻列表（添加 is_local_duplicate 和 duplicate_of 字段）
        """
        # 找出所有重复对
        duplicates = self.find_duplicates(news_list)
        
        if not duplicates:
            # 没有重复，直接返回
            for news in news_list:
                news['is_local_duplicate'] = False
                news['duplicate_of'] = None
            return news_list
        
        # 构建重复组
        # 使用并查集思想，将相互重复的新闻归为一组
        groups = {}  # {代表索引: [索引列表]}
        parent = {}  # 每个索引的父节点
        
        def find(x):
            if x not in parent:
                parent[x] = x
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[py] = px
        
        # 合并重复对
        for i, j, sim in duplicates:
            union(i, j)
        
        # 构建重复组
        for i in range(len(news_list)):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)
        
        # 标记重复项
        for news in news_list:
            news['is_local_duplicate'] = False
            news['duplicate_of'] = None
        
        for root, group in groups.items():
            if len(group) <= 1:
                continue
            
            # 找到组内最早的新闻作为主新闻（保留最早发布的）
            try:
                group_sorted = sorted(group, key=lambda idx: news_list[idx]['published_at'])
                master_idx = group_sorted[0]  # 最早的
            except:
                # 如果排序失败，使用第一个
                master_idx = min(group)
            
            # 标记其他为重复
            for idx in group:
                if idx != master_idx:
                    news_list[idx]['is_local_duplicate'] = True
                    news_list[idx]['duplicate_of'] = master_idx
                    news_list[idx]['duplicate_reason'] = f"本地去重：与第{master_idx+1}条新闻相似"
        
        return news_list
    
    def get_dedup_stats(self, news_list: List[dict]) -> dict:
        """获取去重统计信息"""
        total = len(news_list)
        duplicates = sum(1 for n in news_list if n.get('is_local_duplicate', False))
        unique = total - duplicates
        
        return {
            'total': total,
            'unique': unique,
            'duplicates': duplicates,
            'dedup_rate': f"{duplicates/total*100:.1f}%" if total > 0 else "0%"
        }


# 示例用法
if __name__ == '__main__':
    dedup = LocalDeduplicator(similarity_threshold=0.7)
    
    # 测试案例
    news_list = [
        {
            'title': '易理华旗下 Trend Research 今日增持 4.6 万枚 ETH，约合 1.37 亿美元',
            'published_at': datetime.now()
        },
        {
            'title': '易理华旗下Trend Research增持46,379枚ETH，价值1.37亿美元',
            'published_at': datetime.now()
        },
        {
            'title': 'BTC 突破 10 万美元大关',
            'published_at': datetime.now()
        }
    ]
    
    # 测试相似度计算
    sim = dedup.calculate_similarity(news_list[0]['title'], news_list[1]['title'])
    print(f"标题相似度: {sim:.2f}")
    
    # 测试去重标记
    news_list = dedup.mark_duplicates(news_list)
    
    print("\n去重结果:")
    for i, news in enumerate(news_list, 1):
        status = "❌ 重复" if news['is_local_duplicate'] else "✅ 保留"
        print(f"{i}. {status} - {news['title'][:50]}...")
    
    # 统计
    stats = dedup.get_dedup_stats(news_list)
    print(f"\n统计: {stats}")
