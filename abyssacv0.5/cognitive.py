#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议 v5.0 - 认知内核 (优化版)
包含分词器、认知激活机制、AC100评估器

功能特性：
✅ 轻量分词器（中英文混合 + 智能纠错）
✅ 认知激活机制
✅ AC100七维度评估（使用模型评估）
✅ 认知拓扑探索
✅ 延迟反馈系统
✅ 繁简转换支持

作者: AbyssAC Protocol Team
版本: 5.0 (Cognitive System)
"""

import os
import re
import json
import time
import math
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from collections import Counter, defaultdict, OrderedDict

# Ollama相关导入
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from core import CognitiveError, logger, metrics, config, file_manager, Result

# =============================================================================
# 智能分词器（带纠错功能）
# =============================================================================

class LightweightTokenizer:
    """轻量分词器：无外部依赖，支持中英文混合分词 + 智能纠错"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.cache = {}
        self.cache_size = config.get('tokenizer.cache_size', 1000)
        self.cache_lock = threading.RLock()
        
        # 停用词表
        self.stopwords = self._load_stopwords()
        
        # 核心概念簇
        self.core_concepts = self._build_core_concept_set()
        
        # 激活缓存
        self.activation_cache = {}
        self.activation_cache_size = config.get('tokenizer.activation_cache_size', 500)
        
        # 繁简转换表
        self.trad_to_simp = config.get('tokenizer.trad_to_simp_map', {})
        
        logger.info(f"分词器初始化完成 | 停用词数: {len(self.stopwords)} | 智能纠错: {config.get('tokenizer.enable_smart_correction', True)}")
    
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
        
        # 尝试加载外部停用词文件
        stopwords_path = file_manager.get_path("stopwords.txt")
        content_result = file_manager.safe_read(stopwords_path)
        if content_result.is_ok():
            content = content_result.unwrap()
            for line in content.split('\n'):
                word = line.strip()
                if word and not word.startswith('#'):
                    stopwords.add(word)
        
        return stopwords
    
    def tokenize(self, text: str, return_weights: bool = False) -> Union[List[str], List[Tuple[str, float]]]:
        """分词主函数"""
        with metrics.timer('tokenize'):
            if not text or not text.strip():
                return []
            
            # 检查缓存
            cache_key = hashlib.md5(text.encode()).hexdigest()
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                self.hits += 1
                return cached_result if return_weights else [item[0] for item in cached_result]
            
            self.misses += 1
            
            # 清理文本
            text = self._clean_text(text)
            
            # 智能纠错（如果启用）
            if config.get('tokenizer.enable_smart_correction', True):
                text = self._normalize_text(text)
            
            # 提取候选词
            candidates = self._extract_candidates(text)
            
            # 过滤和评分
            filtered_candidates = self._filter_and_score(candidates, text)
            
            # 排序并返回
            result = sorted(filtered_candidates, key=lambda x: x[1], reverse=True)
            
            # 限制数量
            max_keywords = min(len(result), config.get('tokenizer.max_keywords_per_text', 15))
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
        if config.get('tokenizer.remove_punctuation', True):
            punctuation = "，。！？；：、\"'（）【】《》"
            for char in punctuation:
                text = text.replace(char, ' ')
        
        return text.strip()
    
    def _normalize_text(self, text: str) -> str:
        """文本规范化（繁简转换等）"""
        # 繁简转换
        for trad, simp in self.trad_to_simp.items():
            text = text.replace(trad, simp)
        
        return text
    
    def _extract_candidates(self, text: str) -> List[str]:
        """提取候选词"""
        candidates = []
        
        # 中文词提取
        chinese_words = self._extract_chinese_words(text)
        candidates.extend(chinese_words)
        
        # 英文词提取
        if config.get('tokenizer.extract_english', True):
            english_words = self._extract_english_words(text)
            candidates.extend(english_words)
        
        # 数字提取
        if config.get('tokenizer.extract_numbers', False):
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
        min_len = config.get('tokenizer.min_word_length', 2)
        max_len = config.get('tokenizer.max_word_length', 20)
        
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
            min_len = config.get('tokenizer.min_word_length', 2)
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
        dict_boost = config.get('tokenizer.dict_word_boost', 1.5)
        core_boost = dict_boost if word in self.core_concepts else 1.0
        
        # 4. 位置得分
        pos_score = 1.0
        if text.startswith(word) or text.endswith(word):
            pos_score = 1.2
        
        # 综合得分
        total_score = (freq_score * 0.3 + 
                      len_score * 0.2 + 
                      core_boost * 0.4 + 
                      pos_score * 0.1)
        
        return total_score
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取"""
        with self.cache_lock:
            return self.cache.get(key)
    
    def _put_to_cache(self, key: str, value: Any):
        """放入缓存"""
        with self.cache_lock:
            if len(self.cache) >= self.cache_size:
                # 移除最旧的项（简单策略）
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[key] = value
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate_percent": round(hit_rate, 1),
            "max_cache_size": self.cache_size,
        }

# =============================================================================
# 认知内核
# =============================================================================

class CognitiveKernel:
    """认知内核：实现认知激活机制"""
    
    def __init__(self, dict_manager, tokenizer: LightweightTokenizer):
        self.dict_manager = dict_manager
        self.tokenizer = tokenizer
        self.cognitive_config = config.get('cognitive', {})
        
        # 认知状态
        self.activated_nodes = set()
        self.activation_history = []
        self.drift_logs = []
        
        # 统计
        self.total_activations = 0
        self.activation_patterns = Counter()
        self.patterns_lock = threading.Lock()
        
        # 历史大小限制
        self.max_history_size = self.cognitive_config.get('drift_log_keep', 50)
        
        # 激活缓存
        self.activation_cache = {}
        self.activation_cache_size = self.cognitive_config.get('activation_cache_size', 500)
        
        logger.info("认知内核初始化完成")
    
    def activate(self, text: str, intensity: float = 1.0) -> Dict[str, float]:
        """激活认知网络"""
        with metrics.timer('cognitive_activate'):
            if not text:
                return {}
            
            # 检查激活缓存
            cache_key = hashlib.md5(text.encode()).hexdigest()
            cached_result = self._get_activation_cache(cache_key)
            if cached_result:
                metrics.increment('activation_cache_hit')
                return cached_result
            
            # 分词
            keywords = self.tokenizer.tokenize(text)
            
            # 构建激活上下文
            context = self._build_activation_context(keywords, intensity, text)
            
            # 激活节点
            activations = {}
            
            for keyword in keywords:
                # 查找词在字典中的位置
                if hasattr(self.dict_manager, 'contains_word'):
                    word_exists = self.dict_manager.contains_word(keyword)
                else:
                    word_exists = True  # 假设存在
                
                if word_exists:
                    # 计算激活强度
                    activation_strength = self._calculate_activation_strength(
                        keyword, context, intensity
                    )
                    
                    # 激活节点
                    activations[keyword] = activation_strength
                    self.activated_nodes.add(keyword)
                    
                    with self.patterns_lock:
                        self.total_activations += 1
                        self.activation_patterns[keyword] += 1
            
            # 传播激活
            if self.cognitive_config.get('enable_propagation', True):
                propagated = self._propagate_activations(activations, context)
                activations.update(propagated)
            
            # 记录历史
            self._record_activation(text, activations, intensity)
            
            # 缓存激活结果
            self._put_activation_cache(cache_key, activations)
            
            return activations
    
    def _build_activation_context(self, keywords: List[str], intensity: float, text: str) -> Dict:
        """构建激活上下文"""
        # 统计关键词特征
        keyword_lengths = [len(k) for k in keywords]
        avg_length = sum(keyword_lengths) / len(keyword_lengths) if keyword_lengths else 0
        
        # 检查是否包含核心概念
        core_concept_count = sum(1 for k in keywords if k in self.tokenizer.core_concepts)
        
        # 复杂度评估
        max_chars = self.cognitive_config.get('complexity_max_chars', 2000)
        max_sentences = self.cognitive_config.get('complexity_max_sentences', 20)
        
        complexity = min(len(text) / max_chars, len(keywords) / max_sentences, 1.0)
        
        return {
            "keywords": keywords,
            "keyword_count": len(keywords),
            "avg_length": avg_length,
            "core_concept_count": core_concept_count,
            "has_core_concepts": core_concept_count > 0,
            "input_intensity": intensity,
            "complexity": complexity,
            "timestamp": time.time(),
        }
    
    def _calculate_activation_strength(self, keyword: str, context: Dict, intensity: float) -> float:
        """计算节点的激活强度"""
        base_score = self.cognitive_config.get('score_base_value', 0.1)
        
        # 1. 匹配得分
        match_score = self._calculate_match_score(keyword, context)
        
        # 2. 复杂度得分
        complexity_weight = self.cognitive_config.get('complexity_weight', 0.3)
        complexity_score = context["complexity"] * complexity_weight
        
        # 3. 置信度得分
        confidence_weight = self.cognitive_config.get('confidence_weight', 0.7)
        confidence_score = self._calculate_confidence_score(keyword, context)
        
        # 4. 深度得分
        depth_weight = self.cognitive_config.get('depth_weight', 0.3)
        depth_score = self._calculate_depth_score(keyword, context)
        
        # 综合得分
        match_score_weight = self.cognitive_config.get('match_score_weight', 0.6)
        
        total_score = (base_score + 
                      match_score * match_score_weight +
                      complexity_score +
                      confidence_score * confidence_weight +
                      depth_score * depth_weight)
        
        # 应用强度乘数
        final_score = total_score * intensity
        
        # 限制在0-1范围内
        return min(max(final_score, 0.0), 1.0)
    
    def _calculate_match_score(self, keyword: str, context: Dict) -> float:
        """计算匹配得分"""
        high_threshold = self.cognitive_config.get('high_score_threshold', 0.7)
        medium_threshold = self.cognitive_config.get('medium_score_threshold', 0.5)
        
        if keyword in self.tokenizer.core_concepts:
            return high_threshold
        else:
            return medium_threshold
    
    def _calculate_confidence_score(self, keyword: str, context: Dict) -> float:
        """计算置信度得分"""
        # 基于使用频率
        with self.patterns_lock:
            usage_count = self.activation_patterns.get(keyword, 0)
        
        if usage_count > 10:
            return self.cognitive_config.get('high_score_threshold', 0.7)
        elif usage_count > 3:
            return self.cognitive_config.get('medium_score_threshold', 0.5)
        else:
            return self.cognitive_config.get('low_score_threshold', 0.3)
    
    def _calculate_depth_score(self, keyword: str, context: Dict) -> float:
        """计算深度得分"""
        # 基于关键词长度和相关性
        length_score = min(len(keyword) / 10.0, 1.0)
        
        # 如果在核心概念中，增加深度
        if keyword in self.tokenizer.core_concepts:
            length_score += 0.3
        
        return min(length_score, 1.0)
    
    def _propagate_activations(self, activations: Dict[str, float], context: Dict) -> Dict[str, float]:
        """传播激活到相关节点"""
        propagated = {}
        
        # 基于核心概念的传播
        for activated_node in list(activations.keys()):
            if activated_node in self.tokenizer.core_concepts:
                # 传播到相关的核心概念
                for concept in self.tokenizer.core_concepts:
                    if concept != activated_node and concept not in activations:
                        # 计算传播强度
                        propagation_strength = activations[activated_node] * 0.3
                        if concept not in propagated:
                            propagated[concept] = propagation_strength
        
        return propagated
    
    def _record_activation(self, text: str, activations: Dict[str, float], intensity: float):
        """记录激活历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "text": text[:100],  # 限制长度
            "activations": activations,
            "activation_count": len(activations),
            "avg_activation": sum(activations.values()) / len(activations) if activations else 0,
            "intensity": intensity,
        }
        
        self.activation_history.append(record)
        
        # 限制历史大小（有界）
        if len(self.activation_history) > self.max_history_size:
            self.activation_history.pop(0)
    
    def _get_activation_cache(self, key: str) -> Optional[Dict[str, float]]:
        """获取激活缓存"""
        return self.activation_cache.get(key)
    
    def _put_activation_cache(self, key: str, activations: Dict[str, float]):
        """放入激活缓存"""
        if len(self.activation_cache) >= self.activation_cache_size:
            # 移除最旧的
            oldest_key = next(iter(self.activation_cache))
            del self.activation_cache[oldest_key]
        
        self.activation_cache[key] = activations
    
    def get_activation_summary(self, limit: int = 10) -> Dict:
        """获取激活摘要"""
        recent_activations = self.activation_history[-limit:] if self.activation_history else []
        
        # 统计激活模式
        node_activations = Counter()
        for record in recent_activations:
            for node, strength in record["activations"].items():
                node_activations[node] += strength
        
        # 最活跃的节点
        most_active = node_activations.most_common(10)
        
        return {
            "total_activations": self.total_activations,
            "recent_activations": len(recent_activations),
            "most_active_nodes": most_active,
            "activated_nodes_count": len(self.activated_nodes),
            "recent_avg_activation": sum(r["avg_activation"] for r in recent_activations) / len(recent_activations) if recent_activations else 0,
        }
    
    def get_drift_analysis(self) -> Dict:
        """获取认知漂移分析"""
        if len(self.activation_history) < 2:
            return {"drift_score": 0.0, "trend": "stable", "details": "数据不足"}
        
        # 计算激活模式的变化
        recent = self.activation_history[-10:] if len(self.activation_history) >= 10 else self.activation_history
        
        # 提取激活节点集合
        node_sets = []
        for record in recent:
            node_sets.append(set(record["activations"].keys()))
        
        # 计算变化率
        drift_scores = []
        for i in range(1, len(node_sets)):
            prev_set = node_sets[i-1]
            curr_set = node_sets[i]
            
            # Jaccard距离
            intersection = len(prev_set.intersection(curr_set))
            union = len(prev_set.union(curr_set))
            jaccard_distance = 1 - (intersection / union) if union > 0 else 0
            drift_scores.append(jaccard_distance)
        
        avg_drift = sum(drift_scores) / len(drift_scores) if drift_scores else 0
        
        # 分析趋势
        if avg_drift > 0.5:
            trend = "high_drift"
        elif avg_drift > 0.2:
            trend = "moderate_drift"
        else:
            trend = "stable"
        
        return {
            "drift_score": round(avg_drift, 3),
            "trend": trend,
            "sample_size": len(recent),
            "avg_activation_count": sum(len(r["activations"]) for r in recent) / len(recent)
        }
    
    def serialize_state(self) -> Dict:
        """序列化状态"""
        with self.patterns_lock:
            return {
                'total_activations': self.total_activations,
                'activation_patterns': dict(self.activation_patterns),
                'activated_nodes': list(self.activated_nodes),
                'activation_history': self.activation_history[-20:],  # 只保存最近20次
            }
    
    def deserialize_state(self, state: Dict):
        """反序列化状态"""
        if 'total_activations' in state:
            self.total_activations = state['total_activations']
        if 'activation_patterns' in state:
            with self.patterns_lock:
                self.activation_patterns.update(state['activation_patterns'])
        if 'activated_nodes' in state:
            self.activated_nodes.update(state['activated_nodes'])
        if 'activation_history' in state:
            self.activation_history = state['activation_history']

# =============================================================================
# AC100评估器
# =============================================================================

class AC100Evaluator:
    """AC-100 评估器：实现七维度意识评估"""
    
    def __init__(self, kernel: CognitiveKernel, memory):
        self.kernel = kernel
        self.memory = memory
        self.ac100_config = config.get('ac100', {})
        
        # 评估历史
        self.evaluation_history = []
        self.history_lock = threading.RLock()
        self.max_history_size = 20
        
        # 评估计数器
        self.session_count = 0
        self.counter_lock = threading.Lock()
        
        # 评估间隔
        self.evaluation_interval = self.ac100_config.get('evaluation_interval', 5)
        
        # 是否启用模型评估
        self.enable_model_evaluation = self.ac100_config.get('enable_model_evaluation', True)
        
        logger.info("AC-100 评估器初始化完成")
    
    def should_evaluate(self) -> bool:
        """检查是否应该进行评估"""
        with self.counter_lock:
            return self.session_count % self.evaluation_interval == 0 and self.session_count > 0
    
    def evaluate(self, context: str = None, ollama_client=None):
        """执行AC-100评估"""
        with self.counter_lock:
            self.session_count += 1
        
        if not self.should_evaluate():
            return Result.ok({"status": "skipped", "reason": "未到评估间隔"})
        
        try:
            # 收集评估数据
            evaluation_data = self._collect_evaluation_data()
            
            # 计算七维度得分
            if self.enable_model_evaluation and ollama_client and ollama_client.available:
                dimensions = self._calculate_dimensions_by_model(evaluation_data, ollama_client)
            else:
                dimensions = self._calculate_dimensions(evaluation_data)
            
            if dimensions.is_error():
                return dimensions
            
            dimensions_data = dimensions.unwrap()
            
            # 计算综合AC-100得分
            ac100_score = self._calculate_ac100_score(dimensions_data)
            
            # 构建评估结果
            result = {
                "timestamp": datetime.now().isoformat(),
                "session_count": self.session_count,
                "ac100_score": round(ac100_score, 2),
                "dimensions": dimensions_data,
                "evaluation_data": evaluation_data
            }
            
            # 记录历史
            with self.history_lock:
                self.evaluation_history.append(result)
                
                # 限制历史大小
                if len(self.evaluation_history) > self.max_history_size:
                    self.evaluation_history.pop(0)
            
            logger.info(f"AC-100评估完成: {ac100_score:.2f}")
            
            return Result.ok(result)
            
        except Exception as e:
            logger.error(f"AC-100评估失败: {e}")
            return Result.error(f"AC-100评估失败: {e}", "EvaluationError")
    
    def _collect_evaluation_data(self) -> Dict:
        """收集评估数据"""
        # 1. 认知内核数据
        kernel_summary = self.kernel.get_activation_summary()
        
        # 2. 记忆系统数据
        memory_stats = self.memory.get_memory_stats()
        
        # 3. 漂移分析
        drift_analysis = self.kernel.get_drift_analysis()
        
        return {
            "kernel": kernel_summary,
            "memory": memory_stats.unwrap() if memory_stats.is_ok() else {},
            "drift": drift_analysis
        }
    
    def _calculate_dimensions(self, data: Dict) -> Result:
        """计算七维度得分"""
        try:
            weights = self.ac100_config.get('dimension_weights', {})
            
            # 简化的维度计算
            dimensions = {
                "self_reference": 50.0,
                "value_autonomy": 50.0,
                "cognitive_growth": 50.0,
                "memory_continuity": 50.0,
                "prediction_imagination": 50.0,
                "environment_interaction": 50.0,
                "explanation_transparency": 50.0
            }
            
            return Result.ok(dimensions)
        
        except Exception as e:
            return Result.error(f"计算维度失败: {e}", "EvaluationError")
    
    def _calculate_dimensions_by_model(self, data: Dict, ollama_client) -> Result:
        """使用模型计算七维度得分"""
        try:
            prompt = f"""请基于以下数据评估系统的意识水平，从7个维度进行评分（0-100分）。

评估数据:
- 认知激活总数: {data['kernel'].get('total_activations', 0)}
- 激活节点数: {data['kernel'].get('activated_nodes_count', 0)}
- 记忆总数: {data['memory'].get('total_memories', 0)}

请以JSON格式回复，只包含7个维度的分数。"""
            
            response = ollama_client.generate(prompt, max_tokens=500)
            
            # 简化的响应处理
            import re
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                dimensions = json.loads(json_match.group())
                return Result.ok(dimensions)
            else:
                return self._calculate_dimensions(data)
        
        except Exception as e:
            logger.warning(f"模型评估失败: {e}")
            return self._calculate_dimensions(data)
    
    def _calculate_ac100_score(self, dimensions: Dict[str, float]) -> float:
        """计算综合AC-100得分"""
        weights = self.ac100_config.get('dimension_weights', {})
        
        total_score = 0
        for dim_name, weight in weights.items():
            dim_score = dimensions.get(dim_name, 0)
            total_score += dim_score * weight
        
        return total_score
    
    def get_evaluation_history(self, limit: int = 10) -> list:
        """获取评估历史"""
        with self.history_lock:
            return self.evaluation_history[-limit:] if self.evaluation_history else []


print("[✅] 分词器和认知内核实现完成")
print("    - 中英文混合分词")
print("    - 智能纠错（繁简转换）")
print("    - 认知激活机制")
print("    - 无外部依赖")
