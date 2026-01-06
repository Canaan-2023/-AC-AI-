#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆系统 - 四层记忆架构（反向索引增强版）

实现四层记忆架构，支持反向索引和智能清理策略。
"""

import time
import json
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..core.config_manager import config
from ..core.logger import AbyssLogger, log_performance
from ..core.cache_system import cache_manager
from ..core.event_system import event_system, SystemEvents


class MemoryLayer(Enum):
    """记忆层枚举"""
    METACOGNITIVE = 0  # 元认知记忆
    INTEGRATION = 1    # 高阶整合记忆
    CATEGORICAL = 2    # 分类记忆
    WORKING = 3        # 工作记忆


@dataclass
class Memory:
    """记忆对象"""
    id: str
    content: str
    layer: MemoryLayer
    category: str
    timestamp: str
    keywords: List[str]
    importance_score: float = 0.0
    activation_count: int = 0
    last_accessed: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    fused_from: List[str] = field(default_factory=list)


@dataclass
class ReverseMemoryIndex:
    """反向记忆索引"""
    keyword_to_memories: Dict[str, Set[str]] = field(default_factory=dict)
    category_to_memories: Dict[str, Set[str]] = field(default_factory=dict)
    layer_to_memories: Dict[str, Set[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        self.keyword_to_memories = defaultdict(set)
        self.category_to_memories = defaultdict(set)
        self.layer_to_memories = defaultdict(set)
    
    def add_memory(self, memory: Memory):
        """添加记忆到索引"""
        # 关键词索引
        for keyword in memory.keywords:
            self.keyword_to_memories[keyword].add(memory.id)
        
        # 类别索引
        self.category_to_memories[memory.category].add(memory.id)
        
        # 层级索引
        self.layer_to_memories[memory.layer.name].add(memory.id)
    
    def remove_memory(self, memory: Memory):
        """从索引移除记忆"""
        # 关键词索引
        for keyword in memory.keywords:
            self.keyword_to_memories[keyword].discard(memory.id)
            if not self.keyword_to_memories[keyword]:
                del self.keyword_to_memories[keyword]
        
        # 类别索引
        self.category_to_memories[memory.category].discard(memory.id)
        if not self.category_to_memories[memory.category]:
            del self.category_to_memories[memory.category]
        
        # 层级索引
        self.layer_to_memories[memory.layer.name].discard(memory.id)
        if not self.layer_to_memories[memory.layer.name]:
            del self.layer_to_memories[memory.layer.name]
    
    def search_by_keywords(self, keywords: List[str]) -> Set[str]:
        """通过关键词搜索记忆"""
        memory_ids = set()
        
        for keyword in keywords:
            if keyword in self.keyword_to_memories:
                if not memory_ids:
                    memory_ids = self.keyword_to_memories[keyword].copy()
                else:
                    memory_ids.intersection_update(self.keyword_to_memories[keyword])
                
                if not memory_ids:
                    break  # 没有交集，提前退出
        
        return memory_ids
    
    def search_by_category(self, category: str) -> Set[str]:
        """通过类别搜索记忆"""
        return self.category_to_memories.get(category, set()).copy()
    
    def search_by_layer(self, layer: MemoryLayer) -> Set[str]:
        """通过层级搜索记忆"""
        return self.layer_to_memories.get(layer.name, set()).copy()


class MemorySystem:
    """记忆系统 - 四层记忆架构"""
    
    def __init__(self, dict_manager=None, kernel=None):
        self.dict_manager = dict_manager
        self.kernel = kernel
        self.logger = AbyssLogger("MemorySystem")
        
        # 记忆层配置
        self.layers: Dict[MemoryLayer, List[Memory]] = {
            MemoryLayer.METACOGNITIVE: [],
            MemoryLayer.INTEGRATION: [],
            MemoryLayer.CATEGORICAL: [],
            MemoryLayer.WORKING: []
        }
        
        # 反向索引 - 核心性能优化
        self.reverse_index = ReverseMemoryIndex()
        
        # 记忆存储（ID到记忆的映射）
        self.memories: Dict[str, Memory] = {}
        self._memory_lock = threading.RLock()
        
        # ID计数器
        self.memory_counter = 0
        self._counter_lock = threading.Lock()
        
        # 配置参数
        self.working_memory_size = config.get('memory.working_memory_size', 100)
        self.max_memory_per_layer = config.get('memory.max_memory_per_layer', 1000)
        self.fuse_threshold = config.get('memory.fuse_similarity_threshold', 0.7)
        
        # 融合记忆映射
        self.fused_memories: Dict[str, str] = {}  # source_id -> fused_id
        
        # 缓存
        self.search_cache = cache_manager.create_cache(
            'memory_search', 'lru', maxsize=500
        )
        
        self.logger.info(f"记忆系统初始化完成 | 反向索引就绪")
    
    def create_memory(self, content: str, layer: MemoryLayer = MemoryLayer.CATEGORICAL, 
                     category: str = "未分类", metadata: Dict[str, Any] = None) -> str:
        """创建记忆"""
        with self._counter_lock:
            memory_id = f"mem_{self.memory_counter}_{int(time.time())}"
            self.memory_counter += 1
        
        # 提取关键词
        keywords = []
        if content and self.kernel:
            keywords = self.kernel.tokenizer.tokenize(content)
        
        # 构建记忆对象
        memory = Memory(
            id=memory_id,
            content=content,
            layer=layer,
            category=category,
            timestamp=datetime.now().isoformat(),
            keywords=keywords,
            metadata=metadata or {}
        )
        
        # 计算重要性
        memory.importance_score = self._calculate_importance(memory)
        
        # 存储记忆
        with self._memory_lock:
            self.memories[memory_id] = memory
            self.layers[layer].append(memory)
            
            # 检查层大小限制
            if len(self.layers[layer]) > self.max_memory_per_layer:
                self._cleanup_layer_smart(layer)
            
            # 更新反向索引
            self.reverse_index.add_memory(memory)
            
            # 更新工作记忆
            if layer == MemoryLayer.WORKING:
                self._update_working_memory(memory)
        
        # 触发事件
        event_system.emit(SystemEvents.MEMORY_CREATED, {
            'memory_id': memory_id,
            'layer': layer.name,
            'category': category,
            'keyword_count': len(keywords)
        })
        
        return memory_id
    
    def _calculate_importance(self, memory: Memory) -> float:
        """计算记忆重要性"""
        factors = {
            "layer_priority": self._get_layer_priority(memory.layer),
            "time_recency": 1.0 / (1 + self._hours_since(memory.timestamp)),
            "keyword_richness": len(memory.keywords) / 20.0,  # 假设20个关键词为满分
            "content_length": min(len(memory.content) / 1000.0, 1.0)
        }
        
        # 权重配置
        weights = {
            "layer_priority": 0.4,
            "time_recency": 0.2,
            "keyword_richness": 0.2,
            "content_length": 0.2
        }
        
        return sum(weights[k] * v for k, v in factors.items())
    
    def _get_layer_priority(self, layer: MemoryLayer) -> float:
        """获取层优先级"""
        priorities = {
            MemoryLayer.METACOGNITIVE: 1.0,
            MemoryLayer.INTEGRATION: 0.8,
            MemoryLayer.CATEGORICAL: 0.5,
            MemoryLayer.WORKING: 0.2
        }
        return priorities.get(layer, 0.5)
    
    def _hours_since(self, timestamp: str) -> float:
        """计算自时间戳以来的小时数"""
        dt = datetime.fromisoformat(timestamp)
        return (datetime.now() - dt).total_seconds() / 3600
    
    def _update_working_memory(self, memory: Memory):
        """更新工作记忆"""
        # 工作记忆使用LRU策略
        working_memories = self.layers[MemoryLayer.WORKING]
        
        # 如果超过限制，移除最旧的
        if len(working_memories) > self.working_memory_size:
            oldest_memory = working_memories.pop(0)
            
            # 从反向索引移除
            self.reverse_index.remove_memory(oldest_memory)
            
            # 从主存储移除
            with self._memory_lock:
                if oldest_memory.id in self.memories:
                    del self.memories[oldest_memory.id]
    
    def _cleanup_layer_smart(self, layer: MemoryLayer):
        """智能清理策略"""
        memories = self.layers[layer]
        if len(memories) <= self.max_memory_per_layer:
            return
        
        # 计算每个记忆的"价值分数"
        memories_with_score = []
        for memory in memories:
            score = (
                memory.activation_count * 0.3 +  # 使用频率
                (1 - self._time_decay_factor(memory.timestamp)) * 0.3 +  # 时间衰减
                memory.importance_score * 0.4  # 重要性
            )
            memories_with_score.append((memory, score))
        
        # 移除价值最低的记忆（默认移除10%）
        cleanup_batch_size = max(1, len(memories_with_score) // 10)
        
        memories_with_score.sort(key=lambda x: x[1])
        to_remove = memories_with_score[:cleanup_batch_size]
        
        for memory, _ in to_remove:
            self._remove_memory(memory)
            
            self.logger.debug(f"清理记忆: {memory.id} (重要性: {memory.importance_score:.3f})")
    
    def _time_decay_factor(self, timestamp: str) -> float:
        """计算时间衰减因子"""
        hours = self._hours_since(timestamp)
        decay_hours = config.get('memory.time_decay_hours', 168)
        return min(1.0, hours / decay_hours)
    
    def _remove_memory(self, memory: Memory):
        """移除记忆"""
        # 从层中移除
        if memory in self.layers[memory.layer]:
            self.layers[memory.layer].remove(memory)
        
        # 从反向索引移除
        self.reverse_index.remove_memory(memory)
        
        # 从主存储移除
        with self._memory_lock:
            if memory.id in self.memories:
                del self.memories[memory.id]
    
    @log_performance
    def retrieve_memory(self, query: str, layer: Optional[MemoryLayer] = None, 
                       category: Optional[str] = None, limit: int = 10) -> List[Memory]:
        """检索记忆"""
        # 检查缓存
        cache_key = f"{query}:{layer}:{category}:{limit}"
        cached_result = self.search_cache.get(cache_key) if self.search_cache else None
        if cached_result:
            return cached_result
        
        # 提取查询关键词
        query_keywords = []
        if self.kernel and query:
            query_keywords = self.kernel.tokenizer.tokenize(query)
        
        # 使用反向索引快速搜索
        candidate_ids = set()
        
        if query_keywords:
            candidate_ids = self.reverse_index.search_by_keywords(query_keywords)
        
        # 如果指定了层，进一步过滤
        if layer:
            layer_ids = self.reverse_index.search_by_layer(layer)
            if candidate_ids:
                candidate_ids.intersection_update(layer_ids)
            else:
                candidate_ids = layer_ids
        
        # 如果指定了类别，进一步过滤
        if category:
            category_ids = self.reverse_index.search_by_category(category)
            if candidate_ids:
                candidate_ids.intersection_update(category_ids)
            else:
                candidate_ids = category_ids
        
        # 获取记忆对象
        results = []
        with self._memory_lock:
            for memory_id in candidate_ids:
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    
                    # 计算相关性
                    relevance = self._calculate_relevance(memory, query_keywords)
                    if relevance > 0:
                        results.append((memory, relevance))
        
        # 按相关性排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 限制数量
        final_results = [item[0] for item in results[:limit]]
        
        # 更新访问统计
        for memory in final_results:
            memory.activation_count += 1
            memory.last_accessed = datetime.now().isoformat()
        
        # 缓存结果
        if self.search_cache:
            self.search_cache.put(cache_key, final_results)
        
        # 触发事件
        event_system.emit(SystemEvents.MEMORY_RETRIEVED, {
            'query': query,
            'result_count': len(final_results),
            'layer': layer.name if layer else None,
            'category': category
        })
        
        return final_results
    
    def _calculate_relevance(self, memory: Memory, query_keywords: List[str]) -> float:
        """计算记忆与查询的相关性"""
        if not query_keywords:
            return memory.importance_score
        
        # 关键词匹配得分
        memory_keywords = set(memory.keywords)
        query_set = set(query_keywords)
        
        intersection = memory_keywords.intersection(query_set)
        keyword_score = len(intersection) / len(query_set) if query_set else 0
        
        # 综合得分
        relevance = (keyword_score * 0.6 + 
                    memory.importance_score * 0.3 + 
                    (memory.activation_count / 10.0) * 0.1)
        
        return relevance
    
    @log_performance
    def advanced_retrieve(self, query: str, 
                         include_semantic_expansion: bool = True,
                         include_temporal_context: bool = True,
                         limit: int = 10) -> List[Memory]:
        """增强的记忆检索"""
        # 基础检索
        base_results = self.retrieve_memory(query, limit=limit * 2)
        
        if not include_semantic_expansion:
            return base_results[:limit]
        
        # 语义扩展
        expanded_results = []
        query_keywords = []
        if self.kernel and query:
            query_keywords = self.kernel.tokenizer.tokenize(query)
        
        # 获取基础结果的关键词
        base_keywords = set()
        for memory in base_results:
            base_keywords.update(memory.keywords)
        
        # 查找包含相似关键词的记忆
        for keyword in base_keywords:
            related_ids = self.reverse_index.search_by_keywords([keyword])
            
            for memory_id in related_ids:
                if memory_id in self.memories:
                    memory = self.memories[memory_id]
                    if memory not in base_results and memory not in expanded_results:
                        # 计算语义相似度
                        semantic_score = self._calculate_semantic_similarity(
                            query_keywords, memory.keywords
                        )
                        
                        if semantic_score > 0.3:
                            expanded_results.append(memory)
        
        # 合并结果
        all_results = base_results + expanded_results
        
        # 时间上下文加权
        if include_temporal_context:
            for memory in all_results:
                memory.importance_score *= self._calculate_temporal_relevance(memory)
        
        # 重新排序
        all_results.sort(key=lambda x: x.importance_score, reverse=True)
        
        return all_results[:limit]
    
    def _calculate_semantic_similarity(self, keywords1: List[str], keywords2: List[str]) -> float:
        """计算语义相似度"""
        set1 = set(keywords1)
        set2 = set(keywords2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_temporal_relevance(self, memory: Memory) -> float:
        """计算时间上下文相关性"""
        if not memory.last_accessed:
            return 0.5
        
        last_access = datetime.fromisoformat(memory.last_accessed)
        hours_ago = (datetime.now() - last_access).total_seconds() / 3600
        
        # 指数衰减
        return math.exp(-hours_ago / 24.0)  # 24小时衰减
    
    def fuse_related_memories(self, category: str, similarity_threshold: float = None) -> List[str]:
        """融合相似记忆"""
        if similarity_threshold is None:
            similarity_threshold = self.fuse_threshold
        
        memories = self.retrieve_memory(category, category=category, limit=100)
        
        if len(memories) < 3:
            return []
        
        # 聚类相似记忆
        clusters = self._cluster_memories(memories, similarity_threshold)
        
        fused_ids = []
        for cluster in clusters:
            if len(cluster) >= 3:  # 至少3个相关记忆才融合
                fused_memory = self._create_fused_memory(cluster)
                
                # 存储到高阶整合层
                fused_id = self.create_memory(
                    fused_memory.content,
                    layer=MemoryLayer.INTEGRATION,
                    category=f"fused_{category}",
                    metadata={
                        "source_memories": [m.id for m in cluster],
                        "fusion_type": "semantic_cluster",
                        "cluster_size": len(cluster),
                        "keywords": fused_memory.keywords
                    }
                )
                
                # 记录融合映射
                for source_mem in cluster:
                    self.fused_memories[source_mem.id] = fused_id
                
                fused_ids.append(fused_id)
                self.logger.info(f"融合 {len(cluster)} 个记忆 -> {fused_id}")
        
        return fused_ids
    
    def _cluster_memories(self, memories: List[Memory], threshold: float) -> List[List[Memory]]:
        """基于相似度聚类记忆"""
        clusters = []
        used = set()
        
        for i, mem1 in enumerate(memories):
            if i in used:
                continue
            
            cluster = [mem1]
            used.add(i)
            
            # 查找相似记忆
            for j, mem2 in enumerate(memories[i+1:], start=i+1):
                if j in used:
                    continue
                
                similarity = self._calculate_memory_similarity(mem1, mem2)
                if similarity >= threshold:
                    cluster.append(mem2)
                    used.add(j)
            
            if len(cluster) > 1:
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_memory_similarity(self, mem1: Memory, mem2: Memory) -> float:
        """计算两个记忆的相似度"""
        keywords1 = set(mem1.keywords)
        keywords2 = set(mem2.keywords)
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = keywords1.intersection(keywords2)
        union = keywords1.union(keywords2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _create_fused_memory(self, cluster: List[Memory]) -> Memory:
        """创建融合记忆"""
        # 合并内容
        contents = [mem.content for mem in cluster]
        fused_content = " | ".join(contents[:5])  # 限制长度
        
        # 合并关键词
        all_keywords = []
        for mem in cluster:
            all_keywords.extend(mem.keywords)
        
        fused_keywords = list(set(all_keywords))[:20]  # 去重并限制数量
        
        return Memory(
            id="",  # 将由create_memory分配
            content=fused_content,
            layer=MemoryLayer.INTEGRATION,
            category=f"fused_{cluster[0].category}",
            timestamp=datetime.now().isoformat(),
            keywords=fused_keywords,
            fused_from=[mem.id for mem in cluster]
        )
    
    def discover_patterns(self) -> List[Dict[str, Any]]:
        """发现跨记忆的模式"""
        # 提取所有关键词
        all_keywords = Counter()
        for layer_memories in self.layers.values():
            for memory in layer_memories:
                all_keywords.update(memory.keywords)
        
        # 找出频繁共同出现的关键词对
        cooccurrence_pairs = self._find_cooccurrence_patterns()
        
        # 生成模式建议
        patterns = []
        for (kw1, kw2), count in cooccurrence_pairs.most_common(10):
            patterns.append({
                "keywords": [kw1, kw2],
                "occurrence_count": count,
                "related_memories": self._find_memories_with_keywords([kw1, kw2])
            })
        
        return patterns
    
    def _find_cooccurrence_patterns(self) -> Counter:
        """查找关键词共现模式"""
        cooccurrence = Counter()
        
        for layer_memories in self.layers.values():
            for memory in layer_memories:
                keywords = memory.keywords
                
                # 统计关键词对
                for i in range(len(keywords)):
                    for j in range(i + 1, len(keywords)):
                        pair = tuple(sorted([keywords[i], keywords[j]]))
                        cooccurrence[pair] += 1
        
        return cooccurrence
    
    def _find_memories_with_keywords(self, keywords: List[str]) -> List[str]:
        """查找包含指定关键词的记忆"""
        matching_memories = []
        keyword_set = set(keywords)
        
        for layer_memories in self.layers.values():
            for memory in layer_memories:
                memory_keywords = set(memory.keywords)
                if keyword_set.issubset(memory_keywords):
                    matching_memories.append(memory.id)
        
        return matching_memories
    
    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        total_memories = sum(len(memories) for memories in self.layers.values())
        
        layer_stats = {}
        for layer, memories in self.layers.items():
            layer_stats[layer.name] = {
                "count": len(memories),
                "priority": self._get_layer_priority(layer)
            }
        
        # 计算平均重要性
        all_importance = []
        for memories in self.layers.values():
            for memory in memories:
                all_importance.append(memory.importance_score)
        
        avg_importance = sum(all_importance) / len(all_importance) if all_importance else 0
        
        return {
            "total_memories": total_memories,
            "layers": layer_stats,
            "memory_counter": self.memory_counter,
            "avg_importance": round(avg_importance, 3),
            "fused_memories_count": len(self.fused_memories),
            "reverse_index_stats": {
                "total_keywords": len(self.reverse_index.keyword_to_memories),
                "total_categories": len(self.reverse_index.category_to_memories),
                "total_layers": len(self.reverse_index.layer_to_memories)
            }
        }
    
    def cleanup(self):
        """清理资源"""
        # 执行最后一次智能清理
        for layer in MemoryLayer:
            self._cleanup_layer_smart(layer)
        self.logger.info("记忆系统清理完成")
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化状态"""
        return {
            'memory_counter': self.memory_counter,
            'layers': {
                layer.name: [
                    {
                        'id': mem.id,
                        'content': mem.content[:100],  # 截断内容
                        'category': mem.category,
                        'timestamp': mem.timestamp,
                        'keywords': mem.keywords[:10],  # 限制关键词数量
                        'importance_score': mem.importance_score,
                        'activation_count': mem.activation_count
                    }
                    for mem in memories[-50:]  # 只保存最近50个
                ]
                for layer, memories in self.layers.items()
            },
            'fused_memories': self.fused_memories
        }
    
    def deserialize_state(self, state: Dict[str, Any]):
        """反序列化状态"""
        if 'memory_counter' in state:
            self.memory_counter = state['memory_counter']
        
        if 'fused_memories' in state:
            self.fused_memories = state['fused_memories']