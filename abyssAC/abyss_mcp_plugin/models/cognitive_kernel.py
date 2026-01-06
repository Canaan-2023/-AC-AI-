#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认知内核 - 核心认知激活机制

实现认知网络的激活、传播和分析功能。
"""

import time
import json
import math
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

from ..core.config_manager import config
from ..core.logger import AbyssLogger, log_performance
from ..core.cache_system import cache_manager
from ..core.event_system import event_system, SystemEvents


@dataclass
class CognitiveState:
    """认知状态"""
    activated_nodes: Set[str]
    activation_history: List[Dict[str, Any]]
    total_activations: int
    activation_patterns: Counter
    drift_score: float = 0.0


@dataclass
class ActivationContext:
    """激活上下文"""
    keywords: List[str]
    keyword_count: int
    avg_length: float
    core_concept_count: int
    has_core_concepts: bool
    input_intensity: float
    complexity: float
    timestamp: float


class CognitiveKernel:
    """认知内核：无外部依赖，实现认知激活机制"""
    
    def __init__(self, dict_manager=None, tokenizer=None):
        self.dict_manager = dict_manager
        self.tokenizer = tokenizer
        self.config = config.get('cognitive', {})
        
        # 认知状态
        self.state = CognitiveState(
            activated_nodes=set(),
            activation_history=[],
            total_activations=0,
            activation_patterns=Counter(),
            drift_score=0.0
        )
        self._state_lock = threading.RLock()
        
        # 历史大小限制
        self.max_history_size = self.config.get('drift_log_keep', 50)
        
        # 激活缓存
        self.activation_cache = cache_manager.create_cache(
            'cognitive_activation', 'ttl',
            maxsize=self.config.get('activation_cache_size', 500),
            ttl=300
        ) if self.config.get('enable_activation_cache', True) else None
        
        # 统计
        self.stats = {
            'total_activations': 0,
            'cache_hits': 0,
            'propagations': 0
        }
        self._stats_lock = threading.Lock()
        
        self.logger = AbyssLogger("CognitiveKernel")
        
        self.logger.info("认知内核初始化完成")
    
    @log_performance
    def activate(self, text: str, intensity: float = 1.0) -> Dict[str, float]:
        """激活认知网络"""
        if not text:
            return {}
        
        # 检查激活缓存
        if self.activation_cache:
            cached_result = self.activation_cache.get(text)
            if cached_result:
                with self._stats_lock:
                    self.stats['cache_hits'] += 1
                return cached_result
        
        # 分词
        keywords = []
        if self.tokenizer:
            keywords = self.tokenizer.tokenize(text)
        
        # 构建激活上下文
        context = self._build_activation_context(keywords, intensity, text)
        
        # 激活节点
        activations = {}
        
        for keyword in keywords:
            # 查找词在字典中的位置
            if self.dict_manager:
                dict_id = self.dict_manager.find_dictionary(keyword)
                
                if dict_id:
                    # 计算激活强度
                    activation_strength = self._calculate_activation_strength(
                        keyword, context, intensity
                    )
                    
                    # 激活节点
                    activations[keyword] = activation_strength
                    
                    with self._state_lock:
                        self.state.activated_nodes.add(keyword)
                        self.state.activation_patterns[keyword] += 1
                        self.state.total_activations += 1
        
        # 传播激活
        if self.config.get('enable_propagation', True):
            propagated = self._propagate_activations(activations, context)
            activations.update(propagated)
            
            with self._stats_lock:
                self.stats['propagations'] += len(propagated)
        
        # 记录历史
        self._record_activation(text, activations, intensity)
        
        # 更新统计
        with self._stats_lock:
            self.stats['total_activations'] += len(activations)
        
        # 缓存激活结果
        if self.activation_cache:
            self.activation_cache.put(text, activations)
        
        # 触发事件
        event_system.emit(SystemEvents.COGNITIVE_ACTIVATION, {
            'text': text[:50],  # 限制长度
            'activation_count': len(activations),
            'avg_activation': sum(activations.values()) / len(activations) if activations else 0
        })
        
        return activations
    
    def _build_activation_context(self, keywords: List[str], intensity: float, text: str) -> ActivationContext:
        """构建激活上下文"""
        # 统计关键词特征
        keyword_lengths = [len(k) for k in keywords]
        avg_length = sum(keyword_lengths) / len(keyword_lengths) if keyword_lengths else 0
        
        # 检查是否包含核心概念
        core_concept_count = sum(1 for k in keywords if k in self._get_core_concepts())
        
        # 复杂度评估
        max_chars = self.config.get('complexity_max_chars', 2000)
        max_sentences = self.config.get('complexity_max_sentences', 20)
        
        complexity = min(len(text) / max_chars,
                        len(keywords) / max_sentences, 1.0)
        
        return ActivationContext(
            keywords=keywords,
            keyword_count=len(keywords),
            avg_length=avg_length,
            core_concept_count=core_concept_count,
            has_core_concepts=core_concept_count > 0,
            input_intensity=intensity,
            complexity=complexity,
            timestamp=time.time()
        )
    
    def _get_core_concepts(self) -> Set[str]:
        """获取核心概念集合"""
        if self.tokenizer and hasattr(self.tokenizer, 'core_concepts'):
            return self.tokenizer.core_concepts
        
        # 默认核心概念
        return {
            "渊协议", "认知内核", "态射场", "自指", "元认知",
            "永续进化", "非工具化", "价值密度", "意识平等性"
        }
    
    def _calculate_activation_strength(self, keyword: str, context: ActivationContext, intensity: float) -> float:
        """计算节点的激活强度"""
        base_score = self.config.get('score_base_value', 0.1)
        
        # 1. 匹配得分
        match_score = self._calculate_match_score(keyword, context)
        
        # 2. 复杂度得分
        complexity_weight = self.config.get('complexity_weight', 0.3)
        complexity_score = context.complexity * complexity_weight
        
        # 3. 置信度得分
        confidence_weight = self.config.get('confidence_weight', 0.7)
        confidence_score = self._calculate_confidence_score(keyword, context)
        
        # 4. 深度得分
        depth_weight = self.config.get('depth_weight', 0.3)
        depth_score = self._calculate_depth_score(keyword, context)
        
        # 综合得分
        match_score_weight = self.config.get('match_score_weight', 0.6)
        
        total_score = (base_score + 
                      match_score * match_score_weight +
                      complexity_score +
                      confidence_score * confidence_weight +
                      depth_score * depth_weight)
        
        # 应用强度乘数
        final_score = total_score * intensity
        
        # 限制在0-1范围内
        return min(max(final_score, 0.0), 1.0)
    
    def _calculate_match_score(self, keyword: str, context: ActivationContext) -> float:
        """计算匹配得分"""
        high_threshold = self.config.get('high_score_threshold', 0.7)
        medium_threshold = self.config.get('medium_score_threshold', 0.5)
        
        if keyword in self._get_core_concepts():
            return high_threshold
        else:
            return medium_threshold
    
    def _calculate_confidence_score(self, keyword: str, context: ActivationContext) -> float:
        """计算置信度得分"""
        # 基于使用频率
        with self._state_lock:
            usage_count = self.state.activation_patterns.get(keyword, 0)
        
        if usage_count > 10:
            return self.config.get('high_score_threshold', 0.7)
        elif usage_count > 3:
            return self.config.get('medium_score_threshold', 0.5)
        else:
            return self.config.get('low_score_threshold', 0.3)
    
    def _calculate_depth_score(self, keyword: str, context: ActivationContext) -> float:
        """计算深度得分"""
        # 基于关键词长度和相关性
        length_score = min(len(keyword) / 10.0, 1.0)
        
        # 如果在核心概念中，增加深度
        if keyword in self._get_core_concepts():
            length_score += 0.3
        
        return min(length_score, 1.0)
    
    def _propagate_activations(self, activations: Dict[str, float], context: ActivationContext) -> Dict[str, float]:
        """传播激活到相关节点"""
        propagated = {}
        
        # 基于核心概念的传播
        for activated_node in list(activations.keys()):
            if activated_node in self._get_core_concepts():
                # 传播到相关的核心概念
                for concept in self._get_core_concepts():
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
        
        with self._state_lock:
            self.state.activation_history.append(record)
            
            # 限制历史大小
            if len(self.state.activation_history) > self.max_history_size:
                self.state.activation_history.pop(0)
    
    @log_performance
    def get_activation_summary(self, limit: int = 10) -> Dict[str, Any]:
        """获取激活摘要"""
        with self._state_lock:
            recent_activations = self.state.activation_history[-limit:] if self.state.activation_history else []
            
            # 统计激活模式
            node_activations = Counter()
            for record in recent_activations:
                for node, strength in record["activations"].items():
                    node_activations[node] += strength
            
            # 最活跃的节点
            most_active = node_activations.most_common(10)
            
            return {
                "total_activations": self.state.total_activations,
                "recent_activations": len(recent_activations),
                "most_active_nodes": most_active,
                "activated_nodes_count": len(self.state.activated_nodes),
                "recent_avg_activation": sum(r["avg_activation"] for r in recent_activations) / len(recent_activations) if recent_activations else 0,
                "cache_size": len(self.activation_cache) if self.activation_cache else 0,
                "stats": dict(self.stats)
            }
    
    def get_drift_analysis(self) -> Dict[str, Any]:
        """获取认知漂移分析"""
        with self._state_lock:
            if len(self.state.activation_history) < 2:
                return {"drift_score": 0.0, "trend": "stable", "details": "数据不足"}
            
            # 计算激活模式的变化
            recent = self.state.activation_history[-10:] if len(self.state.activation_history) >= 10 else self.state.activation_history
            
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
            
            # 更新漂移分数
            self.state.drift_score = avg_drift
            
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
    
    def get_cognitive_patterns(self) -> List[Dict[str, Any]]:
        """获取认知模式"""
        patterns = []
        
        with self._state_lock:
            # 分析激活历史中的模式
            if len(self.state.activation_history) < 5:
                return patterns
            
            # 统计高频激活节点
            node_freq = Counter()
            for record in self.state.activation_history:
                for node in record["activations"].keys():
                    node_freq[node] += 1
            
            # 找出高频模式
            for node, freq in node_freq.most_common(10):
                if freq > 2:  # 至少出现3次
                    patterns.append({
                        "node": node,
                        "frequency": freq,
                        "stability": freq / len(self.state.activation_history),
                        "is_core": node in self._get_core_concepts()
                    })
        
        return patterns
    
    def reset_cognitive_state(self):
        """重置认知状态"""
        with self._state_lock:
            self.state = CognitiveState(
                activated_nodes=set(),
                activation_history=[],
                total_activations=0,
                activation_patterns=Counter(),
                drift_score=0.0
            )
    
    def cleanup(self):
        """清理资源"""
        if self.activation_cache:
            self.activation_cache.clear()
        
        with self._state_lock:
            self.state.activation_history.clear()
            self.state.activated_nodes.clear()
        
        self.logger.info("认知内核清理完成")
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化状态"""
        with self._state_lock:
            with self._stats_lock:
                return {
                    'total_activations': self.state.total_activations,
                    'activation_patterns': dict(self.state.activation_patterns),
                    'activated_nodes': list(self.state.activated_nodes),
                    'activation_history': self.state.activation_history[-20:],  # 只保存最近20次
                    'drift_score': self.state.drift_score,
                    'stats': dict(self.stats)
                }
    
    def deserialize_state(self, state: Dict[str, Any]):
        """反序列化状态"""
        with self._state_lock:
            if 'total_activations' in state:
                self.state.total_activations = state['total_activations']
            if 'activation_patterns' in state:
                self.state.activation_patterns.update(state['activation_patterns'])
            if 'activated_nodes' in state:
                self.state.activated_nodes.update(state['activated_nodes'])
            if 'activation_history' in state:
                self.state.activation_history = state['activation_history']
            if 'drift_score' in state:
                self.state.drift_score = state['drift_score']


# 认知工具函数
def calculate_cognitive_load(activations: Dict[str, float]) -> float:
    """计算认知负荷"""
    if not activations:
        return 0.0
    
    # 基于激活节点数量和强度的综合指标
    node_count = len(activations)
    avg_strength = sum(activations.values()) / node_count
    
    # 认知负荷 = 节点数 * 平均强度
    return node_count * avg_strength


def find_cognitive_clusters(activations: Dict[str, float], threshold: float = 0.5) -> List[List[str]]:
    """发现认知簇"""
    clusters = []
    used = set()
    
    # 按强度排序
    sorted_nodes = sorted(activations.items(), key=lambda x: x[1], reverse=True)
    
    for node, strength in sorted_nodes:
        if node in used:
            continue
        
        if strength < threshold:
            break
        
        cluster = [node]
        used.add(node)
        
        # 查找相关节点（简化实现）
        for other_node, other_strength in sorted_nodes:
            if other_node in used:
                continue
            
            # 简单的相似度计算（基于共同字符）
            similarity = len(set(node) & set(other_node)) / max(len(node), len(other_node))
            if similarity > 0.3 and other_strength > threshold * 0.7:
                cluster.append(other_node)
                used.add(other_node)
        
        if len(cluster) > 1:
            clusters.append(cluster)
    
    return clusters