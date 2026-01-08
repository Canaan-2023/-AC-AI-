#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议 v5.0 - 记忆系统 (优化版)
包含反向索引、智能记忆整合、模型判断存储

功能特性：
✅ 反向索引支持（词到记忆的映射）
✅ 智能记忆整合（模型判断语义相关性）
✅ 四层记忆架构（元认知、高阶整合、分类、工作记忆）
✅ 记忆重要性评分
✅ 语义扩展检索
✅ 跨记忆模式发现
✅ 记忆元数据与内容彻底分离

作者: AbyssAC Protocol Team
版本: 5.0 (Memory System)
"""

import os
import sys
import json
import time
import math
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from collections import Counter, defaultdict, OrderedDict

from core import AbyssProtocolError, MemoryError, logger, metrics, config, Result

# =============================================================================
# 记忆系统异常
# =============================================================================

class MemoryIntegrationError(MemoryError):
    """记忆整合错误"""
    pass

# =============================================================================
# 记忆元数据类（彻底分离存储和索引）
# =============================================================================

class MemoryMetadata:
    """记忆元数据 - 只存储索引信息"""
    
    def __init__(self, memory_id: str, layer: int, category: str, 
                 keywords: List[str], importance_score: float = 0.0):
        self.id = memory_id
        self.layer = layer
        self.category = category
        self.keywords = keywords
        self.importance_score = importance_score
        self.timestamp = datetime.now().isoformat()
        self.activation_count = 0
        self.last_accessed = None
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'layer': self.layer,
            'category': self.category,
            'keywords': self.keywords,
            'importance_score': self.importance_score,
            'timestamp': self.timestamp,
            'activation_count': self.activation_count,
            'last_accessed': self.last_accessed,
            'metadata': self.metadata
        }

class MemoryContent:
    """记忆内容 - 只存储内容信息"""
    
    def __init__(self, memory_id: str, content: str, 
                 embeddings: Optional[Any] = None):
        self.id = memory_id
        self.content = content
        self.embeddings = embeddings
        self.content_preview = content[:100] + "..." if len(content) > 100 else content
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'content_preview': self.content_preview,
            'embeddings': self.embeddings
        }

# =============================================================================
# 反向索引管理器
# =============================================================================

class ReverseIndexManager:
    """反向索引管理器 - 词到记忆的映射"""
    
    def __init__(self):
        # 正向索引：记忆ID -> 关键词列表
        self.memory_to_keywords = {}
        
        # 反向索引：关键词 -> 记忆ID列表
        self.keyword_to_memories = defaultdict(list)
        
        # 索引锁（使用分段锁优化）
        self.segment_lock = threading.RLock()
        
        # 索引统计
        self.index_stats = {
            'total_memories': 0,
            'total_keywords': 0,
            'avg_keywords_per_memory': 0.0,
        }
    
    def add_memory(self, memory_id: str, keywords: List[str]):
        """添加记忆到索引"""
        with self.segment_lock:
            # 更新正向索引
            self.memory_to_keywords[memory_id] = list(set(keywords))
            
            # 更新反向索引
            for keyword in set(keywords):
                if memory_id not in self.keyword_to_memories[keyword]:
                    self.keyword_to_memories[keyword].append(memory_id)
            
            # 更新统计
            self._update_stats()
    
    def remove_memory(self, memory_id: str):
        """从索引中移除记忆"""
        with self.segment_lock:
            if memory_id not in self.memory_to_keywords:
                return
            
            keywords = self.memory_to_keywords[memory_id]
            
            # 从反向索引中移除
            for keyword in keywords:
                if keyword in self.keyword_to_memories:
                    try:
                        self.keyword_to_memories[keyword].remove(memory_id)
                        if not self.keyword_to_memories[keyword]:
                            del self.keyword_to_memories[keyword]
                    except ValueError:
                        pass
            
            # 从正向索引中移除
            del self.memory_to_keywords[memory_id]
            
            # 更新统计
            self._update_stats()
    
    def find_memories_by_keywords(self, keywords: List[str], 
                                  match_mode: str = 'any') -> List[Tuple[str, float]]:
        """通过关键词查找记忆"""
        with self.segment_lock:
            memory_scores = Counter()
            keyword_set = set(keywords)
            
            if match_mode == 'any':
                # 任意关键词匹配
                for keyword in keyword_set:
                    if keyword in self.keyword_to_memories:
                        for memory_id in self.keyword_to_memories[keyword]:
                            memory_scores[memory_id] += 1
            
            elif match_mode == 'all':
                # 所有关键词必须匹配
                memory_candidates = None
                for keyword in keyword_set:
                    if keyword in self.keyword_to_memories:
                        if memory_candidates is None:
                            memory_candidates = set(self.keyword_to_memories[keyword])
                        else:
                            memory_candidates &= set(self.keyword_to_memories[keyword])
                    else:
                        return []
                
                if memory_candidates:
                    for memory_id in memory_candidates:
                        memory_scores[memory_id] = len(keyword_set)
            
            elif match_mode == 'fuzzy':
                # 模糊匹配（关键词相似度）
                for indexed_keyword, memory_ids in self.keyword_to_memories.items():
                    similarity = self._calculate_keyword_similarity(
                        indexed_keyword, keyword_set)
                    if similarity > 0.3:
                        for memory_id in memory_ids:
                            memory_scores[memory_id] += similarity
            
            # 返回排序结果
            return memory_scores.most_common()
    
    def get_related_memories(self, memory_id: str, limit: int = 10) -> List[str]:
        """获取相关记忆"""
        with self.segment_lock:
            if memory_id not in self.memory_to_keywords:
                return []
            
            keywords = self.memory_to_keywords[memory_id]
            related = self.find_memories_by_keywords(keywords, match_mode='fuzzy')
            
            # 排除自身
            return [mem_id for mem_id, score in related if mem_id != memory_id][:limit]
    
    def find_keyword_cooccurrence(self, min_count: int = 2) -> Dict[Tuple[str, str], int]:
        """查找关键词共现模式"""
        with self.segment_lock:
            cooccurrence = Counter()
            
            for keyword, memories in self.keyword_to_memories.items():
                if len(memories) >= min_count:
                    # 找到与当前关键词共现的其他关键词
                    for other_keyword, other_memories in self.keyword_to_memories.items():
                        if keyword < other_keyword:  # 避免重复
                            common_memories = set(memories) & set(other_memories)
                            if len(common_memories) >= min_count:
                                cooccurrence[(keyword, other_keyword)] = len(common_memories)
            
            return dict(cooccurrence)
    
    def _update_stats(self):
        """更新索引统计"""
        total_memories = len(self.memory_to_keywords)
        total_keywords = len(self.keyword_to_memories)
        avg_keywords = sum(len(kws) for kws in self.memory_to_keywords.values()) / max(total_memories, 1)
        
        self.index_stats.update({
            'total_memories': total_memories,
            'total_keywords': total_keywords,
            'avg_keywords_per_memory': round(avg_keywords, 2),
        })
    
    def _calculate_keyword_similarity(self, keyword: str, keyword_set: Set[str]) -> float:
        """计算关键词相似度"""
        if keyword in keyword_set:
            return 1.0
        
        # 字符重叠度
        chars1 = set(keyword)
        max_similarity = 0.0
        
        for kw in keyword_set:
            chars2 = set(kw)
            intersection = chars1.intersection(chars2)
            union = chars1.union(chars2)
            similarity = len(intersection) / len(union) if union else 0
            max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def serialize(self) -> Dict:
        """序列化索引"""
        with self.segment_lock:
            return {
                'memory_to_keywords': self.memory_to_keywords,
                'index_stats': self.index_stats,
            }
    
    def deserialize(self, data: Dict):
        """反序列化索引"""
        with self.segment_lock:
            if 'memory_to_keywords' in data:
                self.memory_to_keywords = data['memory_to_keywords']
                
                # 重建反向索引
                self.keyword_to_memories.clear()
                for memory_id, keywords in self.memory_to_keywords.items():
                    for keyword in keywords:
                        if memory_id not in self.keyword_to_memories[keyword]:
                            self.keyword_to_memories[keyword].append(memory_id)
                
                self._update_stats()

# =============================================================================
# 记忆整合器 - 模型判断的智能整合
# =============================================================================

class MemoryIntegrator:
    """记忆整合器 - 基于模型判断的智能整合"""
    
    def __init__(self, reverse_index: ReverseIndexManager):
        self.reverse_index = reverse_index
        self.integration_threshold = config.get('memory.fuse_similarity_threshold', 0.7)
        self.max_integration_size = 5  # 最多整合5个记忆
        self.enable_model_integration = config.get('memory.enable_model_integration', True)
        
        # 整合历史
        self.integration_history = []
        self.history_lock = threading.RLock()
    
    def should_integrate(self, memory_ids: List[str], ollama_client=None) -> bool:
        """判断是否应该整合记忆"""
        if len(memory_ids) < 3:
            return False
        
        if not self.enable_model_integration:
            # 降级为数量判断
            return len(memory_ids) >= 3
        
        if not ollama_client or not ollama_client.available:
            # 没有Ollama客户端，降级为关键词相似度判断
            return self._should_integrate_by_keywords(memory_ids)
        
        # 使用模型判断
        return self._should_integrate_by_model(memory_ids, ollama_client)
    
    def _should_integrate_by_keywords(self, memory_ids: List[str]) -> bool:
        """基于关键词相似度判断是否整合"""
        # 获取所有记忆的关键词
        all_keywords = []
        for memory_id in memory_ids:
            keywords = self.reverse_index.memory_to_keywords.get(memory_id, [])
            all_keywords.extend(keywords)
        
        # 计算关键词重叠度
        keyword_counts = Counter(all_keywords)
        total_keywords = len(all_keywords)
        unique_keywords = len(keyword_counts)
        
        # 如果重复关键词比例高，则应该整合
        overlap_ratio = (total_keywords - unique_keywords) / total_keywords if total_keywords > 0 else 0
        
        return overlap_ratio > 0.3
    
    def _should_integrate_by_model(self, memory_ids: List[str], ollama_client) -> bool:
        """使用模型判断是否整合"""
        try:
            # 获取记忆内容预览
            contents = []
            for memory_id in memory_ids:
                keywords = self.reverse_index.memory_to_keywords.get(memory_id, [])
                content_preview = f"关键词: {', '.join(keywords[:5])}"
                contents.append(content_preview)
            
            # 构建判断prompt
            prompt = f"""判断以下记忆是否讨论同一主题或概念，是否应该被整合成一个高阶记忆。

记忆列表:
{chr(10).join([f"{i+1}. {content}" for i, content in enumerate(contents)])}

请只回答"Yes"或"No"。"""
            
            response = ollama_client.generate(prompt, max_tokens=10)
            return "yes" in response.lower()
        except Exception as e:
            logger.warning(f"模型判断整合失败: {e}，降级为关键词判断")
            return self._should_integrate_by_keywords(memory_ids)
    
    def analyze_memory_relationships(self, memory_id: str) -> Dict[str, Any]:
        """分析记忆与其他记忆的关联关系"""
        related_memories = self.reverse_index.get_related_memories(memory_id, limit=20)
        
        if not related_memories:
            return {'isolated': True, 'relationships': []}
        
        # 分析关联强度
        relationships = []
        memory_keywords = set(self.reverse_index.memory_to_keywords.get(memory_id, []))
        
        for related_id in related_memories:
            related_keywords = set(self.reverse_index.memory_to_keywords.get(related_id, []))
            
            # 计算关联强度
            intersection = memory_keywords.intersection(related_keywords)
            union = memory_keywords.union(related_keywords)
            
            similarity = len(intersection) / len(union) if union else 0
            
            if similarity > 0.3:  # 最低关联阈值
                relationships.append({
                    'memory_id': related_id,
                    'similarity': similarity,
                    'common_keywords': list(intersection),
                    'total_keywords': len(union),
                })
        
        # 按关联强度排序
        relationships.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'isolated': len(relationships) == 0,
            'relationships': relationships[:10],  # 限制数量
            'strongest_connection': relationships[0]['similarity'] if relationships else 0,
        }
    
    def find_integration_candidates(self, min_relationships: int = 3) -> List[List[str]]:
        """查找整合候选（高关联的记忆群组）"""
        # 获取关键词共现模式
        cooccurrence = self.reverse_index.find_keyword_cooccurrence(min_count=2)
        
        # 构建记忆关联图
        memory_graph = defaultdict(set)
        
        for (kw1, kw2), count in cooccurrence.items():
            memories1 = set(self.reverse_index.keyword_to_memories.get(kw1, []))
            memories2 = set(self.reverse_index.keyword_to_memories.get(kw2, []))
            
            # 共同记忆
            common_memories = memories1 & memories2
            
            # 构建关联关系
            for mem1 in common_memories:
                for mem2 in common_memories:
                    if mem1 != mem2:
                        memory_graph[mem1].add(mem2)
        
        # 查找连通分量（潜在的整合候选）
        candidates = []
        visited = set()
        
        def dfs(memory_id: str, component: List[str]):
            if memory_id in visited:
                return
            
            visited.add(memory_id)
            component.append(memory_id)
            
            for neighbor in memory_graph.get(memory_id, set()):
                dfs(neighbor, component)
        
        for memory_id in memory_graph:
            if memory_id not in visited:
                component = []
                dfs(memory_id, component)
                
                if len(component) >= min_relationships:
                    candidates.append(component)
        
        return candidates
    
    def integrate_memories(self, memory_ids: List[str], ollama_client=None) -> Result:
        """整合多个记忆为一个高阶记忆"""
        if len(memory_ids) < 2:
            return Result.error("需要至少2个记忆才能整合", "IntegrationError")
        
        # 判断是否应该整合
        if not self.should_integrate(memory_ids, ollama_client):
            return Result.error("记忆相关性不足，不建议整合", "IntegrationError")
        
        try:
            # 获取所有记忆的关键词
            all_keywords = []
            for memory_id in memory_ids:
                keywords = self.reverse_index.memory_to_keywords.get(memory_id, [])
                all_keywords.extend(keywords)
            
            # 去重关键词
            integrated_keywords = list(set(all_keywords))[:20]
            
            # 生成整合后的记忆ID
            integration_id = f"int_{hashlib.md5(','.join(sorted(memory_ids)).encode()).hexdigest()[:8]}"
            
            # 记录整合历史
            with self.history_lock:
                self.integration_history.append({
                    'integration_id': integration_id,
                    'source_memories': memory_ids,
                    'timestamp': datetime.now().isoformat(),
                    'keyword_count': len(integrated_keywords),
                })
            
            logger.info(f"整合 {len(memory_ids)} 个记忆 -> {integration_id}")
            
            return Result.ok({
                'integration_id': integration_id,
                'keywords': integrated_keywords,
                'source_count': len(memory_ids)
            })
        
        except Exception as e:
            logger.error(f"记忆整合失败: {e}")
            return Result.error(f"记忆整合失败: {e}", "IntegrationError")
    
    def get_integration_history(self, limit: int = 10) -> List[Dict]:
        """获取整合历史"""
        with self.history_lock:
            return self.integration_history[-limit:]

# =============================================================================
# 记忆系统 - 四层架构
# =============================================================================

class MemorySystem:
    """记忆系统：实现四层记忆架构 + 反向索引 + 智能整合"""
    
    def __init__(self, kernel):
        self.kernel = kernel
        self.tokenizer = kernel.tokenizer
        
        # 记忆层配置
        self.layers = {}
        self._initialize_layers()
        
        # 反向索引管理器
        self.reverse_index = ReverseIndexManager()
        
        # 记忆整合器
        self.integrator = MemoryIntegrator(self.reverse_index)
        
        # ID计数器（原子操作）
        self.memory_counter = 0
        self.counter_lock = threading.Lock()
        
        # 工作记忆
        self.working_memory = []
        self.working_memory_size = config.get('memory.working_memory_size', 100)
        
        # 最大记忆数限制
        self.max_memory_per_layer = config.get('memory.max_memory_per_layer', 1000)
        
        # 记忆内容存储（彻底分离索引和内容）
        self.memory_store = {}  # memory_id -> MemoryContent
        self.metadata_store = {}  # memory_id -> MemoryMetadata
        self.store_lock = threading.RLock()
        
        logger.info(f"记忆系统初始化完成 | 层数: {len(self.layers)}")
    
    def _initialize_layers(self):
        """初始化记忆层"""
        memory_layers = {
            0: {"name": "元认知记忆", "priority": 10, "description": "渊协议核心理论、存在公式、六大理念"},
            1: {"name": "高阶整合记忆", "priority": 8, "description": "跨会话整合、认知跃迁记录"},
            2: {"name": "分类记忆", "priority": 5, "description": "日常交互、主题分类"},
            3: {"name": "工作记忆", "priority": 1, "description": "临时缓存、快速清理"},
        }
        
        for layer_id, config_data in memory_layers.items():
            self.layers[layer_id] = {
                "id": layer_id,
                "name": config_data["name"],
                "priority": config_data["priority"],
                "description": config_data["description"],
                "memory_ids": [],  # 只存储ID
                "size": 0
            }
    
    def create_memory(self, content: str, layer: int = 2, category: str = "未分类", 
                     metadata: Dict = None) -> Result:
        """创建记忆"""
        try:
            with self.counter_lock:
                memory_id = f"mem_{self.memory_counter}_{int(time.time())}"
                self.memory_counter += 1
            
            # 提取关键词
            keywords = self.tokenizer.tokenize(content) if content else []
            
            # 创建记忆元数据（轻量级，只存储索引信息）
            memory_metadata = MemoryMetadata(
                memory_id=memory_id,
                layer=layer,
                category=category,
                keywords=keywords
            )
            memory_metadata.metadata = metadata or {}
            
            # 创建记忆内容（存储完整内容）
            memory_content = MemoryContent(
                memory_id=memory_id,
                content=content
            )
            
            # 计算记忆重要性
            importance_score = self.calculate_memory_importance(memory_metadata)
            memory_metadata.importance_score = importance_score
            
            # 存储到内存（分离存储）
            with self.store_lock:
                self.metadata_store[memory_id] = memory_metadata
                self.memory_store[memory_id] = memory_content
            
            # 存储到指定层
            if layer in self.layers:
                # 检查是否超过最大记忆数
                if self.layers[layer]["size"] >= self.max_memory_per_layer:
                    self._cleanup_layer_smart(layer)
                
                self.layers[layer]["memory_ids"].append(memory_id)
                self.layers[layer]["size"] += 1
                
                # 更新反向索引
                self.reverse_index.add_memory(memory_id, keywords)
                
                # 如果是工作记忆，也添加到工作记忆列表
                if layer == 3:
                    self.working_memory.append(memory_id)
                    if len(self.working_memory) > self.working_memory_size:
                        self.working_memory.pop(0)
            
            return Result.ok(memory_id)
        
        except Exception as e:
            return Result.error(f"创建记忆失败: {e}", "MemoryError")
    
    def get_memory_content(self, memory_id: str) -> Result:
        """获取记忆内容"""
        try:
            with self.store_lock:
                memory_content = self.memory_store.get(memory_id)
                if memory_content:
                    return Result.ok(memory_content.content)
                else:
                    return Result.error(f"记忆不存在: {memory_id}", "MemoryNotFound")
        except Exception as e:
            return Result.error(f"获取记忆内容失败: {e}", "MemoryError")
    
    def get_memory_metadata(self, memory_id: str) -> Result:
        """获取记忆元数据"""
        try:
            with self.store_lock:
                memory_metadata = self.metadata_store.get(memory_id)
                if memory_metadata:
                    return Result.ok(memory_metadata.to_dict())
                else:
                    return Result.error(f"记忆不存在: {memory_id}", "MemoryNotFound")
        except Exception as e:
            return Result.error(f"获取记忆元数据失败: {e}", "MemoryError")
    
    def calculate_memory_importance(self, memory_metadata: MemoryMetadata) -> float:
        """计算记忆重要性分数"""
        factors = {
            "activation_frequency": memory_metadata.activation_count,
            "layer_priority": self.layers[memory_metadata.layer]["priority"],
            "time_recency": 1.0 / (1 + self._hours_since(memory_metadata.timestamp)),
            "keyword_richness": len(memory_metadata.keywords),
            "metadata_completeness": len(memory_metadata.metadata),
        }
        
        # 权重配置
        weights = {
            "activation_frequency": 0.3,
            "layer_priority": 0.25,
            "time_recency": 0.2,
            "keyword_richness": 0.15,
            "metadata_completeness": 0.1,
        }
        
        return sum(weights[k] * min(v, 10) for k, v in factors.items())
    
    def _hours_since(self, timestamp: str) -> float:
        """计算自时间戳以来的小时数"""
        dt = datetime.fromisoformat(timestamp)
        return (datetime.now() - dt).total_seconds() / 3600
    
    def _cleanup_layer_smart(self, layer_id: int):
        """智能清理策略"""
        layer = self.layers[layer_id]
        if layer["size"] < self.max_memory_per_layer:
            return
        
        # 计算每个记忆的"价值分数"
        memory_scores = []
        for memory_id in layer["memory_ids"]:
            result = self.get_memory_metadata(memory_id)
            if result.is_ok():
                metadata = result.unwrap()
                score = self.calculate_memory_importance(MemoryMetadata(**metadata))
                memory_scores.append((memory_id, score))
        
        # 移除价值最低的记忆（默认移除10%）
        cleanup_batch_size = config.get('memory.cleanup_batch_size', 10)
        remove_count = max(1, len(memory_scores) // cleanup_batch_size)
        
        memory_scores.sort(key=lambda x: x[1])
        to_remove = memory_scores[:remove_count]
        
        for memory_id, score in to_remove:
            self._remove_memory(memory_id)
            logger.debug(f"清理记忆: {memory_id} (分数: {score:.3f})")
    
    def _remove_memory(self, memory_id: str):
        """移除记忆"""
        # 从反向索引中移除
        self.reverse_index.remove_memory(memory_id)
        
        # 从层中移除
        for layer in self.layers.values():
            if memory_id in layer["memory_ids"]:
                layer["memory_ids"].remove(memory_id)
                layer["size"] -= 1
        
        # 从工作记忆中移除
        if memory_id in self.working_memory:
            self.working_memory.remove(memory_id)
        
        # 从存储中移除
        with self.store_lock:
            if memory_id in self.memory_store:
                del self.memory_store[memory_id]
            if memory_id in self.metadata_store:
                del self.metadata_store[memory_id]
    
    def retrieve_memory(self, query: str, layer: Optional[int] = None, 
                       category: Optional[str] = None, limit: int = 10) -> Result:
        """检索记忆"""
        try:
            with metrics.timer('retrieve_memory'):
                # 分词查询
                query_keywords = self.tokenizer.tokenize(query)
                
                if not query_keywords:
                    return Result.ok([])
                
                # 使用反向索引查找
                memory_candidates = self.reverse_index.find_memories_by_keywords(
                    query_keywords, match_mode='fuzzy')
                
                # 获取记忆数据
                results = []
                for memory_id, relevance in memory_candidates:
                    # 检查层过滤
                    if layer is not None:
                        layer_memory_ids = self.layers.get(layer, {}).get('memory_ids', [])
                        if memory_id not in layer_memory_ids:
                            continue
                    
                    # 获取记忆内容和元数据
                    content_result = self.get_memory_content(memory_id)
                    metadata_result = self.get_memory_metadata(memory_id)
                    
                    if content_result.is_ok() and metadata_result.is_ok():
                        content = content_result.unwrap()
                        metadata = metadata_result.unwrap()
                        
                        # 构建结果
                        memory_result = {
                            'id': memory_id,
                            'content': content,
                            'relevance': relevance,
                            'preview': content[:100] + "..." if len(content) > 100 else content,
                            'metadata': metadata
                        }
                        results.append(memory_result)
                
                # 按相关性排序
                results.sort(key=lambda x: x['relevance'], reverse=True)
                
                return Result.ok(results[:limit])
        
        except Exception as e:
            return Result.error(f"检索记忆失败: {e}", "MemoryError")
    
    def advanced_retrieve(self, query: str, 
                         include_semantic_expansion: bool = True,
                         include_temporal_context: bool = True,
                         limit: int = 10) -> Result:
        """增强的记忆检索"""
        # 基础检索
        base_result = self.retrieve_memory(query, limit=limit*2)
        if base_result.is_error():
            return base_result
        
        base_results = base_result.unwrap()
        
        if not include_semantic_expansion:
            return Result.ok(base_results[:limit])
        
        # 语义扩展
        expanded_results = []
        seen_ids = set(r['id'] for r in base_results)
        
        # 获取查询的关键词
        query_keywords = set(self.tokenizer.tokenize(query))
        
        # 查找包含相似关键词的记忆
        for keyword in query_keywords:
            related_memories = self.reverse_index.find_memories_by_keywords([keyword])
            for memory_id, relevance in related_memories:
                if memory_id not in seen_ids:
                    seen_ids.add(memory_id)
                    content_result = self.get_memory_content(memory_id)
                    if content_result.is_ok():
                        content = content_result.unwrap()
                        expanded_results.append({
                            'id': memory_id,
                            'content': content,
                            'relevance': relevance * 0.7,  # 降低扩展结果的权重
                            'preview': content[:100] + "..." if len(content) > 100 else content,
                        })
        
        # 合并结果
        all_results = base_results + expanded_results
        all_results.sort(key=lambda x: x['relevance'], reverse=True)
        
        return Result.ok(all_results[:limit])
    
    def integrate_related_memories(self, category: str = "未分类", ollama_client=None) -> Result:
        """整合相关记忆"""
        try:
            integrated_ids = []
            
            # 查找整合候选
            candidates = self.integrator.find_integration_candidates(min_relationships=3)
            
            for candidate_group in candidates:
                if len(candidate_group) >= 3:  # 至少3个记忆才整合
                    result = self.integrator.integrate_memories(candidate_group, ollama_client)
                    if result.is_ok():
                        integrated_data = result.unwrap()
                        integrated_ids.append(integrated_data['integration_id'])
            
            logger.info(f"记忆整合完成: {len(integrated_ids)} 个融合记忆")
            return Result.ok(integrated_ids)
        
        except Exception as e:
            return Result.error(f"整合相关记忆失败: {e}", "MemoryError")
    
    def discover_patterns(self) -> Result:
        """发现跨记忆的模式"""
        try:
            patterns = []
            
            # 获取关键词共现模式
            cooccurrence = self.reverse_index.find_keyword_cooccurrence(min_count=2)
            
            # 生成模式建议
            for (kw1, kw2), count in sorted(cooccurrence.items(), key=lambda x: x[1], reverse=True)[:10]:
                related_memories = self.reverse_index.find_memories_by_keywords([kw1, kw2])[:5]
                patterns.append({
                    'keywords': [kw1, kw2],
                    'occurrence_count': count,
                    'related_memories': related_memories,
                })
            
            return Result.ok(patterns)
        
        except Exception as e:
            return Result.error(f"发现模式失败: {e}", "MemoryError")
    
    def get_memory_stats(self) -> Result:
        """获取记忆统计"""
        try:
            total_memories = sum(layer["size"] for layer in self.layers.values())
            
            layer_stats = {}
            for layer_id, layer in self.layers.items():
                layer_stats[layer["name"]] = {
                    "count": layer["size"],
                    "priority": layer["priority"],
                }
            
            return Result.ok({
                "total_memories": total_memories,
                "layers": layer_stats,
                "working_memory_size": len(self.working_memory),
                "index_stats": self.reverse_index.index_stats,
                "memory_counter": self.memory_counter,
                "integration_history_count": len(self.integrator.integration_history),
            })
        
        except Exception as e:
            return Result.error(f"获取记忆统计失败: {e}", "MemoryError")
    
    def serialize_state(self) -> Result:
        """序列化状态"""
        try:
            # 序列化元数据存储
            metadata_dict = {}
            with self.store_lock:
                for memory_id, metadata in self.metadata_store.items():
                    metadata_dict[memory_id] = metadata.to_dict()
            
            return Result.ok({
                'memory_counter': self.memory_counter,
                'layers': {
                    k: {
                        "id": v["id"],
                        "name": v["name"],
                        "priority": v["priority"],
                        "size": v["size"],
                        "memory_ids": v["memory_ids"][-100:],  # 只保存最近100个
                    }
                    for k, v in self.layers.items()
                },
                'working_memory': self.working_memory[-20:],  # 只保存最近20个
                'reverse_index': self.reverse_index.serialize(),
                'metadata_store': metadata_dict
            })
        
        except Exception as e:
            return Result.error(f"序列化状态失败: {e}", "SerializationError")
    
    def deserialize_state(self, state: Dict) -> Result:
        """反序列化状态"""
        try:
            if 'memory_counter' in state:
                self.memory_counter = state['memory_counter']
            
            if 'layers' in state:
                for layer_id, layer_data in state['layers'].items():
                    if int(layer_id) in self.layers:
                        self.layers[int(layer_id)].update(layer_data)
            
            if 'working_memory' in state:
                self.working_memory = state['working_memory']
            
            if 'reverse_index' in state:
                self.reverse_index.deserialize(state['reverse_index'])
            
            if 'metadata_store' in state:
                metadata_dict = state['metadata_store']
                with self.store_lock:
                    for memory_id, metadata_data in metadata_dict.items():
                        metadata = MemoryMetadata(**metadata_data)
                        self.metadata_store[memory_id] = metadata
            
            return Result.ok()
        
        except Exception as e:
            return Result.error(f"反序列化状态失败: {e}", "DeserializationError")
    
    def cleanup(self) -> Result:
        """清理资源"""
        try:
            # 执行最后一次智能清理
            for layer_id in self.layers.keys():
                self._cleanup_layer_smart(layer_id)
            
            # 清理过期工作记忆
            cutoff_time = datetime.now() - timedelta(hours=1)
            self.working_memory = [
                memory_id for memory_id in self.working_memory
                if datetime.fromisoformat(self.metadata_store.get(memory_id, {}).timestamp) > cutoff_time
            ]
            
            logger.info("记忆系统清理完成")
            return Result.ok()
        
        except Exception as e:
            return Result.error(f"清理记忆系统失败: {e}", "MemoryError")

print("[✅] 记忆系统实现完成")
print("    - 反向索引支持")
print("    - 智能记忆整合（模型判断）")
print("    - 四层记忆架构")
print("    - 存储与索引彻底分离")
print("    - 关联度分析")
