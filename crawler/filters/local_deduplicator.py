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
    
    def __init__(self, similarity_threshold: float = 0.50, time_window_hours: int = 24):
        """
        Args:
            similarity_threshold: 相似度阈值 (0-1)，超过此值认为是重复（默认0.50）
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
            
            # 🔧 修复：前导相同的前提是位数（量级）相同
            import math
            
            # 先检查量级是否相同
            if n1 == 0 or n2 == 0:
                return n1 == n2
            
            magnitude1 = int(math.floor(math.log10(abs(n1))))
            magnitude2 = int(math.floor(math.log10(abs(n2))))
            
            # 位数不同，直接返回False（如1000和10不应该相近）
            if magnitude1 != magnitude2:
                return False
            
            # 位数相同，比较前导数字
            normalized1 = n1 / (10 ** magnitude1)
            normalized2 = n2 / (10 ** magnitude2)
            
            # 取前2位有效数字
            leading1 = int(normalized1 * 10)
            leading2 = int(normalized2 * 10)
            
            # 前导相同认为相近
            if leading1 == leading2:
                return True
            
            # 兜底：相对误差<10%
            diff = abs(n1 - n2) / max(n1, n2)
            return diff <= 0.10
            
        except:
            return n1_str == n2_str
    
    def extract_entities(self, title: str) -> Set[str]:
        """
        提取标题中的实体（币种、项目、人名等）
        
        Returns:
            实体集合，例如: {'BTC', 'Sonic', 'Andrew Tate'}
        """
        entities = set()
        
        # 1. 币种代币（2-5个大写字母，常见加密货币）
        # 匹配 BTC, ETH, USDT, ZEC, FLOW 等
        crypto_pattern = r'\b[A-Z]{2,5}\b'
        crypto_matches = re.findall(crypto_pattern, title)
        
        # 过滤掉常见的非币种缩写
        non_crypto = {'ETF', 'CEO', 'CTO', 'FBI', 'SEC', 'USD', 'API', 'NFT', 'DAO', 'DApp', 'ID', 'IP', 'TV', 'AI', 'AR', 'VR'}
        for match in crypto_matches:
            if match not in non_crypto:
                entities.add(match)
        
        # 2. 知名项目/协议（预定义列表）
        known_projects = {
            'Sonic', 'Uniswap', 'Aave', 'Compound', 'MakerDAO', 
            'Curve', 'Balancer', 'SushiSwap', 'PancakeSwap',
            'Hyperliquid', 'Railgun', 'Tornado', 'Aztec',
            'Polygon', 'Arbitrum', 'Optimism', 'Base',
            'Binance', 'Coinbase', 'Kraken', 'Bitfinex',
            'Bithumb', 'Upbit', 'OKX', 'Bybit',
            'OpenSea', 'Blur', 'LooksRare',
            'Metaplanet', 'MicroStrategy', 'Tesla',
            'BlackRock', 'Grayscale', 'Fidelity',
            'DeBot', 'Debot'
        }
        
        # 同时匹配中英文项目名
        known_projects_cn = {
            '币安': 'Binance',
            '火币': 'Huobi',  
            '欧易': 'OKX',
            '慢雾': 'SlowMist',
            '派盾': 'PeckShield'
        }
        
        title_lower = title.lower()
        for proj in known_projects:
            if proj.lower() in title_lower:
                entities.add(proj)
        
        for cn_name, en_name in known_projects_cn.items():
            if cn_name in title:
                entities.add(en_name)
        
        # 3. 人名（两个或以上首字母大写的连续单词）
        # 例如: Andrew Tate, Elon Musk, Sam Bankman-Fried
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        name_matches = re.findall(name_pattern, title)
        entities.update(name_matches)
        
        return entities

    def calculate_similarity(self, title1: str, title2: str) -> float:
        """
        计算两个标题的相似度
        
        使用组合策略：
        0. 🆕 实体检查 - 如果主语实体完全不同，直接判定为不重复
        1. 字串包含检测 (如果完全包含且不冲突，直接高分)
        2. 关键数字近似匹配 - 如果关键数字接近（±5%误差），相似度+0.4
        3. 关键词匹配度 (50%)
        4. 字符串序列相似度 (20%)
        
        Returns:
            相似度分数 (0-1)
        """
        # 🆕 步骤0: 实体检查（防止不相关新闻误判）
        entities1 = self.extract_entities(title1)
        entities2 = self.extract_entities(title2)
        
        # 如果双方都有实体且无交集 → 主语不同 → 不可能重复
        if entities1 and entities2:
            # 🔧 改进：区分核心实体和场所实体
            # 场所实体（交易所/平台）不应作为判断依据
            VENUE_ENTITIES = {
                'Binance', 'Coinbase', 'Kraken', 'Bitfinex',
                'Bithumb', 'Upbit', 'OKX', 'Bybit', 'Huobi',
                'Uniswap', 'PancakeSwap', 'SushiSwap',
                'OpenSea', 'Blur', 'Railgun'
            }
            
            # 过滤掉场所实体，只保留核心实体（币种/项目等）
            core_entities1 = entities1 - VENUE_ENTITIES
            core_entities2 = entities2 - VENUE_ENTITIES
            
            # 如果双方都有核心实体且无交集 → 主语不同 → 不重复
            if core_entities1 and core_entities2:
                common_core = core_entities1 & core_entities2
                if not common_core:
                    # 无共同核心实体，直接返回0（不重复）
                    # print(f"[Entity Check] 不同核心实体: {core_entities1} vs {core_entities2} → 不重复")
                    return 0.0
        
        # 继续原有逻辑
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
            
            # 🔧 移除数字奖励：数字只作为基础特征，不给额外bonus
            num_bonus = 0
        elif not nums1 and not nums2:
            num_sim = 0
            num_bonus = 0
        else:
            num_sim = 0
            num_bonus = 0
        
        # 3. 关键词匹配度
        kw1, kw2 = features1['keywords'], features2['keywords']
        if kw1 and kw2:
            kw_sim = len(kw1 & kw2) / len(kw1 | kw2)
        elif not kw1 and not kw2:
            kw_sim = seq_sim
        else:
            kw_sim = 0
        
        # 🔧 英文专有名词额外加权
        # 中文新闻中的英文词（如Flow、Polymarket）是核心主体，匹配权重应该更高
        english_bonus = 0
        if kw1 and kw2:
            # 通用币种缩写，不给额外加分
            COMMON_CRYPTO = {'BTC', 'ETH', 'USDT', 'USDC', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 
                           'MATIC', 'DOT', 'AVAX', 'LINK', 'UNI', 'ATOM', 'LTC', 'BCH',
                           'CEO', 'CFO', 'CTO', 'AI', 'NFT', 'DeFi', 'DAO', 'ETF'}
            
            # 提取英文词（长度>2，避免is、or等）
            english_kw1 = {w for w in kw1 if w.encode('utf-8').isalpha() and len(w) > 2 and w not in COMMON_CRYPTO}
            english_kw2 = {w for w in kw2 if w.encode('utf-8').isalpha() and len(w) > 2 and w not in COMMON_CRYPTO}
            
            # 共同的英文专有名词
            common_english = english_kw1 & english_kw2
            
            # 每个匹配的英文词给+0.1分，最多+0.2
            if common_english:
                english_bonus = min(0.2, len(common_english) * 0.1)
        
        # 基础权重计算
        # 字符串序列：40%，关键词：45%，数字：15%
        base_similarity = seq_sim * 0.40 + num_sim * 0.15 + kw_sim * 0.45
        
        # 加上英文专有名词奖励
        final_similarity = min(1.0, base_similarity + english_bonus)
        
        return final_similarity

    def calculate_similarity_from_features(self, features1: dict, features2: dict) -> float:
        """
        基于预提取的特征计算相似度 (性能优化版)
        """
        # 0. 包含关系检查（快速通道）
        norm1 = features1['normalized']
        norm2 = features2['normalized']
        
        if norm1 and norm2 and (norm1 in norm2 or norm2 in norm1):
            len1, len2 = len(norm1), len(norm2)
            ratio = min(len1, len2) / max(len1, len2)
            
            if ratio > 0.25:
                nums1, nums2 = features1['numbers'], features2['numbers']
                
                def has_number_conflict(short_nums, long_nums):
                    if not short_nums: return False
                    if not long_nums: return True
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
                
                if len(norm1) < len(norm2):
                    conflict = has_number_conflict(nums1, nums2)
                else:
                    conflict = has_number_conflict(nums2, nums1)
                
                if not conflict:
                    return 0.95
        
        # 1. 字符串序列相似度
        seq_sim = SequenceMatcher(None, features1['normalized'], features2['normalized']).ratio()
        
        # 2. 数字匹配度
        nums1, nums2 = features1['numbers'], features2['numbers']
        if nums1 and nums2:
            exact_matches = len(nums1 & nums2)
            approx_matches = 0
            for n1 in nums1:
                for n2 in nums2:
                    if n1 not in nums2 and n2 not in nums1:
                        if self._numbers_are_close(n1, n2):
                            approx_matches += 1
                            break
            total_matches = exact_matches + approx_matches
            total_numbers = len(nums1 | nums2)
            num_sim = total_matches / total_numbers if total_numbers > 0 else 0
            
            if total_matches >= 2: num_bonus = 0.5
            elif total_matches >= 1: num_bonus = 0.3
            else: num_bonus = 0
        elif not nums1 and not nums2:
            num_sim = 0 # Fixed logic from previous step
            num_bonus = 0
        else:
            num_sim = 0
            num_bonus = 0
        
        # 3. 关键词匹配度
        kw1, kw2 = features1['keywords'], features2['keywords']
        if kw1 and kw2:
            kw_sim = len(kw1 & kw2) / len(kw1 | kw2)
        elif not kw1 and not kw2:
            kw_sim = seq_sim
        else:
            kw_sim = 0
        
        base_similarity = seq_sim * 0.15 + num_sim * 0.25 + kw_sim * 0.6
        return min(1.0, base_similarity + num_bonus)
    
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
        
        if len(news_list) > 1000:
            print(f"[LocalDeduplicator] 开始计算相似度，数据量: {n}")
            
        # --- 优化步骤 1: 预计算特征 & 步骤 2: 动态停用词 ---
        print(f"[LocalDeduplicator] 预计算特征并提取动态停用词...")
        features_list = []
        word_counts = {}
        
        # 1. 提取所有特征并统计词频
        for news in news_list:
            feat = self.extract_key_features(news['title'])
            features_list.append(feat)
            for w in feat['keywords']:
                word_counts[w] = word_counts.get(w, 0) + 1
        
        # 2. 识别高频停用词 (出现率 > 50%)
        # 例如: "比特币", "加密", "Web3" 等在某些垂直领域太常见，失去区分度
        dynamic_stop_words = set()
        if n > 10: # 只有样本量足够时才统计
            high_freq_threshold = n * 0.5
            for w, count in word_counts.items():
                if count > high_freq_threshold:
                    dynamic_stop_words.add(w)
            
            if dynamic_stop_words:
                print(f"[LocalDeduplicator] 发现 {len(dynamic_stop_words)} 个高频动态停用词: {list(dynamic_stop_words)[:10]}...")
                
                # 从特征中移除动态停用词
                for feat in features_list:
                    feat['keywords'] = feat['keywords'] - dynamic_stop_words
        # ----------------------------------------------------

        comparisons = 0
        total_comparisons = (n * (n - 1)) // 2
        
        for i in range(n):
            for j in range(i + 1, n):
                comparisons += 1
                if comparisons % 10000 == 0:
                    print(f"[LocalDeduplicator] 进度: {comparisons}/{total_comparisons} ({comparisons/total_comparisons:.1%})")
                    
                news1 = news_list[i]
                news2 = news_list[j]
                
                # 检查时间窗口
                try:
                    time1 = news1['published_at']
                    time2 = news2['published_at']
                    
                    if isinstance(time1, str):
                        # 处理带时区的 ISO 8601 字符串
                        time1 = time1.replace('Z', '+00:00')
                        time1 = datetime.fromisoformat(time1)
                    if isinstance(time2, str):
                        time2 = time2.replace('Z', '+00:00')
                        time2 = datetime.fromisoformat(time2)
                    
                    
                    # 确保都是 offset-aware 或 offset-naive
                    if time1.tzinfo is None and time2.tzinfo is not None:
                        time1 = time1.replace(tzinfo=time2.tzinfo)
                    elif time1.tzinfo is not None and time2.tzinfo is None:
                        time2 = time2.replace(tzinfo=time1.tzinfo)
                    
                    time_diff = abs((time1 - time2).total_seconds() / 3600)
                    
                    # 🔧 FIX: 无论time_window_hours是多少，每条新闻只和前后2小时内的比较
                    # 这是比较窗口（固定2小时），不同于处理范围(time_window_hours)
                    COMPARISON_WINDOW_HOURS = 2
                    if time_diff > COMPARISON_WINDOW_HOURS:
                        # 优化：列表已按时间倒序排列，一旦超时，后续均超时，直接中断
                        break
                        
                except Exception as e:
                    # 时间解析失败，继续比较 (安全回退)
                    pass
                
                # 计算相似度 (使用预计算的特征)
                similarity = self.calculate_similarity_from_features(features_list[i], features_list[j])
                
                if similarity >= self.similarity_threshold:
                    duplicates.append((i, j, similarity))
                    # print(f"  [发现重复] {similarity:.2f}: {news1['title'][:20]}... <-> {news2['title'][:20]}...")
        
        print(f"[LocalDeduplicator] 完成。发现 {len(duplicates)} 对重复。")
        return duplicates
    
    def mark_duplicates(self, news_list: List[dict]) -> List[dict]:
        """
        标记新闻列表中的重复项
        
        🔧 修复：移除并查集，改为直接one-to-one标记
        原因：并查集的传递性会导致"黑洞效应" - A和B相似、B和C相似，
              并查集会把A、C归为一组，即使A和C完全不相似
        
        新策略：每对重复中，只标记后者为前者的重复，不传递
        
        Args:
            news_list: 新闻列表
        
        Returns:
            标记后的新闻列表（添加 is_local_duplicate 和 duplicate_of 字段）
        """
        # 找出所有重复对
        duplicates = self.find_duplicates(news_list)
        
        # 初始化所有新闻
        for news in news_list:
            news['is_local_duplicate'] = False
            news['duplicate_of'] = None
        
        if not duplicates:
            return news_list
        
        # 🔧关键修复：需要两个集合来彻底阻止链式结构
        # already_duplicate: 已经被标记为duplicate的新闻（不能再被标记）
        # used_as_master: 已经被用作master的新闻（不能再被标记为duplicate）
        already_duplicate = set()
        used_as_master = set()
        
        # 对于每一对(i, j)，让后发布的指向先发布的
        for i, j, similarity in duplicates:
            news_i = news_list[i]
            news_j = news_list[j]
            
            id_i = news_i['id']
            id_j = news_j['id']
            
            # 比较发布时间，让晚的指向早的
            try:
                time_i = news_i['published_at']
                time_j = news_j['published_at']
                
                if isinstance(time_i, str):
                    time_i = datetime.fromisoformat(time_i.replace('Z', '+00:00'))
                if isinstance(time_j, str):
                    time_j = datetime.fromisoformat(time_j.replace('Z', '+00:00'))
                
                # 决定哪个是duplicate，哪个是master
                # i更早 → j指向i (j是duplicate, i是master)
                if time_i <= time_j:
                    duplicate_id = id_j
                    master_id = id_i
                    duplicate_news = news_j
                else:
                    # j更早 → i指向j (i是duplicate, j是master)
                    duplicate_id = id_i
                    master_id = id_j
                    duplicate_news = news_i
                
                # 🆕 Master合并逻辑：
                # 如果duplicate已经是master（有其他新闻指向它），执行合并
                # 1. duplicate不能已经被标记过（A→B后，不能A→C）
                # 2. master不能已经是duplicate（防止C→B, B→A的情况）
                if duplicate_id in already_duplicate or master_id in already_duplicate:
                    continue
                
                # 🆕检查duplicate是否已经作为master
                if duplicate_id in used_as_master:
                    # Master合并：将所有指向duplicate_id的新闻改为指向master_id
                    # 🔧 关键修复：需要验证相似度！
                    for other_news in news_list:
                        if other_news.get('duplicate_of') == duplicate_id:
                            # ⚠️ 重要：验证other_news和master_id的相似度
                            # 只有相似度 >= 阈值时才合并，避免误合并
                            master_news = next((n for n in news_list if n['id'] == master_id), None)
                            if master_news:
                                merge_similarity = self.calculate_similarity(
                                    other_news['title'], 
                                    master_news['title']
                                )
                                if merge_similarity >= self.similarity_threshold:
                                    # 相似度足够，可以合并
                                    other_news['duplicate_of'] = master_id
                                    other_news['duplicate_reason'] = f"本地去重：与新闻ID={master_id}相似(master合并,相似度{merge_similarity:.2f})"
                                # else: 相似度不够，保持原状
                    # 继续将duplicate标记为指向master
                
                # 标记为重复
                duplicate_news['is_local_duplicate'] = True
                duplicate_news['duplicate_of'] = master_id
                duplicate_news['duplicate_reason'] = f"本地去重：与新闻ID={master_id}相似(相似度{similarity:.2f})"
                already_duplicate.add(duplicate_id)
                used_as_master.add(master_id)
            except:
                # 如果时间比较失败，让索引大的指向索引小的
                if i < j:
                    duplicate_id = id_j
                    master_id = id_i
                    duplicate_news = news_j
                else:
                    duplicate_id = id_i
                    master_id = id_j
                    duplicate_news = news_i
                
                # 同样的检查和master合并
                if duplicate_id in already_duplicate or master_id in already_duplicate:
                    continue
                
                # Master合并（添加相似度验证）
                if duplicate_id in used_as_master:
                    for other_news in news_list:
                        if other_news.get('duplicate_of') == duplicate_id:
                            # 验证相似度
                            master_news = next((n for n in news_list if n['id'] == master_id), None)
                            if master_news:
                                merge_similarity = self.calculate_similarity(
                                    other_news['title'], 
                                    master_news['title']
                                )
                                if merge_similarity >= self.similarity_threshold:
                                    other_news['duplicate_of'] = master_id
                                    other_news['duplicate_reason'] = f"本地去重：与新闻ID={master_id}相似(master合并,相似度{merge_similarity:.2f})"
                
                duplicate_news['is_local_duplicate'] = True
                duplicate_news['duplicate_of'] = master_id
                duplicate_news['duplicate_reason'] = f"本地去重：与新闻ID={master_id}相似(相似度{similarity:.2f})"
                already_duplicate.add(duplicate_id)
                used_as_master.add(master_id)
        
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
