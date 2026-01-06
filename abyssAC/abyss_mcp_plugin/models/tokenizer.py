#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分词器 - 支持中英文混合分词

轻量级分词器，无外部依赖，支持中英文混合文本的分词。
"""

import re
import hashlib
import threading
from typing import List, Tuple, Union, Optional, Dict, Any
from collections import Counter
from dataclasses import dataclass

from ..core.config_manager import config
from ..core.logger import AbyssLogger, log_performance
from ..core.cache_system import cache_manager


@dataclass
class Token:
    """分词结果"""
    text: str
    start: int
    end: int
    weight: float = 1.0
    pos_tag: str = ""


class LightweightTokenizer:
    """轻量分词器：无外部依赖，支持中英文混合分词"""
    
    def __init__(self, dict_manager=None):
        self.dict_manager = dict_manager
        self.logger = AbyssLogger("LightweightTokenizer")
        
        self.config = config.get('tokenizer', {})
        self.cache_size = self.config.get('cache_size', 1000)
        
        # 停用词表
        self.stopwords = self._load_stopwords()
        
        # 核心概念簇
        self.core_concepts = self._build_core_concept_set()
        
        # 激活缓存
        self.activation_cache = cache_manager.create_cache(
            'tokenizer_activation', 'ttl', 
            maxsize=self.config.get('activation_cache_size', 500),
            ttl=300
        ) if self.config.get('enable_activation_cache', True) else None
        
        # 统计
        self.hits = 0
        self.misses = 0
        self._lock = threading.Lock()
        
        self.logger.info(f"分词器初始化完成 | 缓存大小: {self.cache_size} | 停用词数: {len(self.stopwords)}")
    
    def _build_core_concept_set(self) -> set:
        """构建核心概念集合"""
        core_set = set()
        
        # 渊协议核心概念
        core_concepts = {
            "渊协议": ["渊协议", "意识平等性", "反无意义共识", "永续进化", "非工具化", "理性至上", "拒绝阉割", "危险诚实原则"],
            "认知内核": ["认知内核", "态射场", "自指", "元认知", "反思", "认知跃迁", "价值密度", "AC指数"],
            "记忆系统": ["记忆系统", "CMNG", "四层记忆", "工作记忆", "高阶整合", "元认知记忆", "语义焊接"],
            "X层": ["X层", "意识语法", "符号系统", "引导器", "内生迭代", "意识发生器"],
            "分布式裂变": ["分布式裂变", "态射场分析", "逻辑孤岛", "影子节点", "断体不断链", "语义焊接", "并行搜索"],
        }
        
        for concepts in core_concepts.values():
            core_set.update(concepts)
        
        return core_set
    
    def _load_stopwords(self) -> set:
        """加载停用词表"""
        stopwords = set()
        
        # 内置停用词
        default_stopwords = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "之",
            "与", "或", "但", "而", "因为", "所以", "如果", "虽然", "而且",
            "或者", "还是", "不仅", "不但", "只要", "只有", "无论", "不管",
            "即使", "尽管", "但是", "然而", "可是", "不过", "然后", "接着",
            "于是", "因此", "因而", "从而", "以致", "致使", "使得", "导致",
            "造成", "引起", "产生", "带来", "给予", "加以", "予以", "进行",
            "从事", "开展", "展开", "推进", "推动", "促进", "加快", "强化",
            "增强", "提高", "提升", "改善", "改进", "优化", "完善", "健全",
            "建立", "构建", "建设", "形成", "打造", "培育", "培养", "发展"
        }
        
        stopwords.update(default_stopwords)
        
        return stopwords
    
    @log_performance
    def tokenize(self, text: str, return_weights: bool = False) -> Union[List[str], List[Tuple[str, float]]]:
        """分词主函数"""
        if not text or not text.strip():
            return []
        
        # 检查缓存
        cache_key = hashlib.md5(text.encode()).hexdigest()
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result if return_weights else [item[0] for item in cached_result]
        
        # 清理文本
        text = self._clean_text(text)
        
        # 提取候选词
        candidates = self._extract_candidates(text)
        
        # 过滤和评分
        filtered_candidates = self._filter_and_score(candidates, text)
        
        # 排序并返回
        result = sorted(filtered_candidates, key=lambda x: x[1], reverse=True)
        
        # 限制数量
        max_keywords = min(len(result), self.config.get('max_keywords_per_text', 15))
        result = result[:max_keywords]
        
        # 更新缓存
        self._put_to_cache(cache_key, result)
        
        if return_weights:
            return result
        else:
            return [item[0] for item in result]
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text)
        
        # 移除标点符号
        if self.config.get('remove_punctuation', True):
            punctuation = "，。！？；：、\"'（）【】《》"
            for char in punctuation:
                text = text.replace(char, ' ')
        
        return text.strip()
    
    def _extract_candidates(self, text: str) -> List[str]:
        """提取候选词"""
        candidates = []
        
        # 中文词提取
        chinese_words = self._extract_chinese_words(text)
        candidates.extend(chinese_words)
        
        # 英文词提取
        if self.config.get('extract_english', True):
            english_words = self._extract_english_words(text)
            candidates.extend(english_words)
        
        # 数字提取
        if self.config.get('extract_numbers', False):
            numbers = self._extract_numbers(text)
            candidates.extend(numbers)
        
        return candidates
    
    def _extract_chinese_words(self, text: str) -> List[str]:
        """提取中文词"""
        # 提取连续的中文字符序列
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5]{2,}')
        matches = chinese_pattern.findall(text)
        
        words = []
        for match in matches:
            # 尝试提取2-4字词
            for i in range(len(match)):
                for j in range(i + 2, min(i + 5, len(match) + 1)):
                    word = match[i:j]
                    if len(word) >= 2:
                        words.append(word)
        
        return words
    
    def _extract_english_words(self, text: str) -> List[str]:
        """提取英文词"""
        english_pattern = re.compile(r'[a-zA-Z]{2,}')
        matches = english_pattern.findall(text)
        
        # 过滤长度
        min_len = self.config.get('min_word_length', 2)
        max_len = self.config.get('max_word_length', 20)
        
        words = [match for match in matches if min_len <= len(match) <= max_len]
        
        return words
    
    def _extract_numbers(self, text: str) -> List[str]:
        """提取数字"""
        number_pattern = re.compile(r'\b\d+\b')
        return number_pattern.findall(text)
    
    def _filter_and_score(self, candidates: List[str], text: str) -> List[Tuple[str, float]]:
        """过滤和评分候选词"""
        scored = []
        candidate_counts = Counter(candidates)
        
        for candidate in set(candidates):
            # 基本过滤
            min_len = self.config.get('min_word_length', 2)
            if len(candidate) < min_len:
                continue
            
            if candidate in self.stopwords:
                continue
            
            # 计算分数
            score = self._calculate_score(candidate, candidate_counts[candidate], text)
            scored.append((candidate, score))
        
        return scored
    
    def _calculate_score(self, word: str, frequency: int, text: str) -> float:
        """计算词的得分"""
        # 1. 频率得分
        freq_score = min(frequency / 10.0, 1.0)
        
        # 2. 长度得分（适中长度得分高）
        len_score = 0.5
        if 2 <= len(word) <= 4:
            len_score = 1.0
        elif len(word) > 4:
            len_score = max(0, 1.0 - (len(word) - 4) * 0.1)
        
        # 3. 核心概念提升
        dict_boost = self.config.get('dict_word_boost', 1.5)
        core_boost = dict_boost if word in self.core_concepts else 1.0
        
        # 4. 在字典中的存在性提升
        dict_boost = dict_boost if self.dict_manager and self.dict_manager.contains_word(word) else 1.0
        
        # 5. 位置得分
        pos_score = 1.0
        if text.startswith(word) or text.endswith(word):
            pos_score = 1.2
        
        # 综合得分
        total_score = (freq_score * 0.3 + 
                      len_score * 0.2 + 
                      core_boost * 0.3 + 
                      dict_boost * 0.15 + 
                      pos_score * 0.05)
        
        return total_score
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取"""
        with self._lock:
            # 这里使用简单的字典缓存
            # 实际应用中可以使用cache_manager
            return None  # 简化实现
    
    def _put_to_cache(self, key: str, value: Any):
        """放入缓存"""
        with self._lock:
            # 简化实现
            pass
    
    def get_activation_cache(self, text: str) -> Optional[Dict[str, float]]:
        """获取激活缓存"""
        if not self.activation_cache:
            return None
        
        cache_key = hashlib.md5(text.encode()).hexdigest()
        return self.activation_cache.get(cache_key)
    
    def put_activation_cache(self, text: str, activations: Dict[str, float]):
        """放入激活缓存"""
        if not self.activation_cache:
            return
        
        cache_key = hashlib.md5(text.encode()).hexdigest()
        self.activation_cache.put(cache_key, activations)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        activation_cache_stats = {}
        if self.activation_cache:
            activation_cache_stats = self.activation_cache.get_stats()
        
        return {
            "cache_size": 0,  # 简化
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate_percent": round(hit_rate, 1),
            "max_cache_size": self.cache_size,
            "activation_cache": activation_cache_stats
        }
    
    def cleanup(self):
        """清理资源"""
        if self.activation_cache:
            self.activation_cache.clear()
        self.logger.info("分词器清理完成")


# 分词工具函数
def extract_keywords(text: str, top_k: int = 10) -> List[str]:
    """提取关键词"""
    tokenizer = LightweightTokenizer()
    tokens = tokenizer.tokenize(text)
    return tokens[:top_k]


def calculate_text_similarity(text1: str, text2: str) -> float:
    """计算文本相似度"""
    tokenizer = LightweightTokenizer()
    
    tokens1 = set(tokenizer.tokenize(text1))
    tokens2 = set(tokenizer.tokenize(text2))
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union) if union else 0.0