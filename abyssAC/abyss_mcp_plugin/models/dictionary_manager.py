#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字典管理器 - 反向索引增强版

实现分布式字典管理和反向索引，大幅提升检索性能。
"""

import os
import json
import time
import hashlib
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from collections import defaultdict, Counter
from dataclasses import dataclass, field

from ..core.config_manager import config
from ..core.logger import AbyssLogger, log_performance
from ..core.cache_system import cache_manager
from ..core.event_system import event_system, SystemEvents


@dataclass
class DictionaryInfo:
    """字典信息"""
    id: str
    path: str
    words: Set[str] = field(default_factory=set)
    size: int = 0
    created: float = 0
    modified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReverseIndexEntry:
    """反向索引条目"""
    word: str
    dict_ids: Set[str] = field(default_factory=set)
    frequency: int = 0
    last_accessed: float = 0


class MorphismAnalyzer:
    """态射场分析器 - 分布式裂变核心"""
    
    def __init__(self, dict_manager: 'DictionaryManager'):
        self.dict_manager = dict_manager
        self.logger = AbyssLogger("MorphismAnalyzer")
        
        # 分析历史
        self.analysis_history = []
        self.max_history_size = config.get('dictionary.analysis_history_size', 20)
        
        # 图缓存
        self.graph_cache = cache_manager.create_cache(
            'morphism_graphs', 'ttl', maxsize=50, ttl=300
        )
        
        # 配置参数
        self.analyzer_params = config.get('dictionary', {})
        
        self.logger.info("态射场分析器初始化完成")
    
    @log_performance
    def analyze_morphism_field(self, dict_info: DictionaryInfo) -> Dict[str, Any]:
        """分析字典的态射场"""
        try:
            # 构建节点列表
            nodes = list(dict_info.words)
            if not nodes:
                return {"error": "字典为空"}
            
            # 检查缓存
            cache_key = f"{dict_info.id}:{hash(str(sorted(nodes)))}"
            cached_result = self.graph_cache.get(cache_key) if self.graph_cache else None
            if cached_result:
                return cached_result
            
            # 构建态射矩阵
            morphism_matrix = self._build_morphism_matrix(dict_info)
            
            # 构建图表示
            graph = self._build_graph_from_morphisms(nodes, morphism_matrix)
            
            # 识别连通分量
            clusters = self._find_connected_components(graph, nodes)
            
            # 识别边缘节点
            edge_nodes = self._identify_edge_nodes(graph, nodes)
            
            # 识别核心态射路径
            core_morphisms = self._identify_core_morphisms(morphism_matrix)
            
            # 分析结果
            analysis_result = {
                "dict_id": dict_info.id,
                "total_nodes": len(nodes),
                "total_edges": sum(len(neighbors) for neighbors in graph.values()) // 2,
                "clusters": clusters,
                "cluster_count": len(clusters),
                "edge_nodes": edge_nodes,
                "edge_node_count": len(edge_nodes),
                "core_morphisms": core_morphisms,
                "core_morphism_count": len(core_morphisms),
                "timestamp": time.time(),
                "graph_density": self._calculate_graph_density(graph, len(nodes))
            }
            
            # 生成裂变建议
            analysis_result["recommendations"] = self._generate_fission_recommendations(analysis_result)
            
            # 缓存结果
            if self.graph_cache:
                self.graph_cache.put(cache_key, analysis_result)
            
            # 记录历史
            self._record_analysis(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"态射场分析失败: {e}")
            return {"error": str(e)}
    
    def _build_morphism_matrix(self, dict_info: DictionaryInfo) -> Dict[str, float]:
        """构建态射矩阵"""
        morphism_matrix = {}
        words = list(dict_info.words)[:100]  # 限制数量
        
        for i in range(len(words)):
            for j in range(i + 1, len(words)):
                word1, word2 = words[i], words[j]
                
                # 计算相似度
                similarity = self._calculate_semantic_similarity(word1, word2)
                
                # 结合使用频率
                freq1 = self.dict_manager.get_word_frequency(word1)
                freq2 = self.dict_manager.get_word_frequency(word2)
                freq_factor = min(freq1, freq2) / max(freq1, freq2, 1)
                
                # 综合权重
                weight = similarity * 0.7 + freq_factor * 0.3
                
                if weight > 0.1:
                    edge = "|".join(sorted([word1, word2]))
                    morphism_matrix[edge] = round(weight, 4)
        
        return morphism_matrix
    
    def _build_graph_from_morphisms(self, nodes: List[str], morphism_matrix: Dict[str, float]) -> Dict[str, List[Tuple[str, float]]]:
        """从态射矩阵构建图结构"""
        graph = {node: [] for node in nodes}
        
        for edge, weight in morphism_matrix.items():
            if "|" in edge:
                node1, node2 = edge.split("|")
                if node1 in graph and node2 in graph:
                    graph[node1].append((node2, weight))
                    graph[node2].append((node1, weight))
        
        return graph
    
    def _find_connected_components(self, graph: Dict[str, List[Tuple[str, float]]], nodes: List[str]) -> List[Dict[str, Any]]:
        """使用DFS识别连通分量"""
        visited = set()
        clusters = []
        isolation_threshold = self.analyzer_params.get('isolation_threshold', 0.1)
        
        for node in nodes:
            if node not in visited:
                component = self._dfs_component(graph, node, visited, isolation_threshold)
                if component:
                    isolation_score = self._calculate_isolation_score(component, graph)
                    clusters.append({
                        "nodes": component,
                        "size": len(component),
                        "is_isolated": isolation_score < isolation_threshold,
                        "isolation_score": isolation_score,
                        "avg_connection_strength": self._calculate_avg_connection(component, graph)
                    })
        
        # 按大小排序
        clusters.sort(key=lambda x: x["size"], reverse=True)
        return clusters
    
    def _dfs_component(self, graph: Dict[str, List[Tuple[str, float]]], start: str, visited: Set[str], threshold: float) -> List[str]:
        """深度优先搜索连通分量"""
        stack = [start]
        component = []
        
        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                component.append(current)
                
                # 添加邻居
                for neighbor, weight in graph.get(current, []):
                    if neighbor not in visited and weight > threshold:
                        stack.append(neighbor)
        
        return component
    
    def _calculate_isolation_score(self, component: List[str], graph: Dict[str, List[Tuple[str, float]]]) -> float:
        """计算簇的隔离程度"""
        if not component:
            return 1.0
        
        internal_connections = 0
        external_connections = 0
        
        for node in component:
            for neighbor, weight in graph.get(node, []):
                if neighbor in component:
                    internal_connections += 1
                else:
                    external_connections += 1
        
        total_connections = internal_connections + external_connections
        if total_connections == 0:
            return 0.0
        
        return external_connections / total_connections
    
    def _calculate_avg_connection(self, component: List[str], graph: Dict[str, List[Tuple[str, float]]]) -> float:
        """计算簇内平均连接强度"""
        if not component or len(component) < 2:
            return 0.0
        
        total_weight = 0
        connection_count = 0
        
        for node in component:
            for neighbor, weight in graph.get(node, []):
                if neighbor in component:
                    total_weight += weight
                    connection_count += 1
        
        return total_weight / connection_count if connection_count > 0 else 0.0
    
    def _identify_edge_nodes(self, graph: Dict[str, List[Tuple[str, float]]], nodes: List[str]) -> List[Dict[str, Any]]:
        """识别边缘节点"""
        edge_nodes = []
        edge_threshold = self.analyzer_params.get('edge_node_threshold', 0.3)
        
        for node in nodes:
            neighbors = graph.get(node, [])
            
            # 计算连接强度
            connection_strength = 0
            if neighbors:
                connection_strength = sum(weight for _, weight in neighbors) / len(neighbors)
            
            # 检查是否是边缘节点
            if len(neighbors) < 3 or connection_strength < edge_threshold:
                edge_nodes.append({
                    "node": node,
                    "connection_count": len(neighbors),
                    "connection_strength": connection_strength,
                    "is_edge": True
                })
        
        # 按连接强度排序
        edge_nodes.sort(key=lambda x: x["connection_strength"])
        return edge_nodes
    
    def _identify_core_morphisms(self, morphism_matrix: Dict[str, float]) -> List[Dict[str, Any]]:
        """识别核心态射路径"""
        core_threshold = self.analyzer_params.get('core_morphism_strength', 0.7)
        core_morphisms = []
        
        for edge, weight in morphism_matrix.items():
            if weight >= core_threshold:
                node1, node2 = edge.split("|")
                core_morphisms.append({
                    "edge": edge,
                    "node1": node1,
                    "node2": node2,
                    "weight": weight,
                    "is_core": True
                })
        
        # 按权重排序
        core_morphisms.sort(key=lambda x: x["weight"], reverse=True)
        return core_morphisms
    
    def _calculate_graph_density(self, graph: Dict[str, List[Tuple[str, float]]], node_count: int) -> float:
        """计算图密度"""
        if node_count < 2:
            return 0.0
        
        edge_count = sum(len(neighbors) for neighbors in graph.values()) // 2
        max_edges = node_count * (node_count - 1) // 2
        
        return edge_count / max_edges if max_edges > 0 else 0.0
    
    def _generate_fission_recommendations(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成裂变建议"""
        recommendations = {
            "fission_needed": False,
            "reason": "",
            "recommended_actions": [],
            "priority": "low"
        }
        
        total_nodes = analysis_result["total_nodes"]
        cluster_count = analysis_result["cluster_count"]
        edge_node_count = analysis_result["edge_node_count"]
        graph_density = analysis_result["graph_density"]
        
        fission_threshold = self.analyzer_params.get('fission_threshold', 0.8)
        max_cluster_size = self.analyzer_params.get('max_cluster_size', 300)
        
        # 规则1: 图密度过低
        if cluster_count > 3 and graph_density < 0.1:
            recommendations["fission_needed"] = True
            recommendations["reason"] = f"检测到{cluster_count}个逻辑孤岛，图密度过低({graph_density:.3f})"
            recommendations["recommended_actions"].append("分离逻辑孤岛到独立字典")
            recommendations["priority"] = "high"
        
        # 规则2: 边缘节点过多
        elif edge_node_count > total_nodes * 0.3:
            recommendations["fission_needed"] = True
            recommendations["reason"] = f"边缘节点过多({edge_node_count}/{total_nodes})"
            recommendations["recommended_actions"].append("剥离边缘节点到辅助字典")
            recommendations["priority"] = "medium"
        
        # 规则3: 核心态射路径清晰但整体过大
        elif (analysis_result["core_morphism_count"] > 10 and total_nodes > max_cluster_size):
            recommendations["fission_needed"] = True
            recommendations["reason"] = f"字典过大({total_nodes}节点)，但核心态射路径清晰"
            recommendations["recommended_actions"].append("保留核心路径，剥离二阶节点")
            recommendations["priority"] = "medium"
        
        return recommendations
    
    def _record_analysis(self, analysis_result: Dict[str, Any]):
        """记录分析历史"""
        self.analysis_history.append(analysis_result)
        
        # 限制历史大小
        if len(self.analysis_history) > self.max_history_size:
            self.analysis_history.pop(0)


class ReverseIndex:
    """反向索引 - 提升检索性能"""
    
    def __init__(self):
        self._index: Dict[str, ReverseIndexEntry] = {}
        self._word_to_dict: Dict[str, Set[str]] = defaultdict(set)
        self._lock = threading.RLock()
        self._stats = {
            'lookups': 0,
            'hits': 0,
            'updates': 0,
            'deletions': 0
        }
    
    def add_word(self, word: str, dict_id: str):
        """添加词到反向索引"""
        with self._lock:
            if word not in self._index:
                self._index[word] = ReverseIndexEntry(word=word)
            
            entry = self._index[word]
            entry.dict_ids.add(dict_id)
            entry.frequency += 1
            entry.last_accessed = time.time()
            
            self._word_to_dict[word].add(dict_id)
            self._stats['updates'] += 1
    
    def remove_word(self, word: str, dict_id: str):
        """从反向索引移除词"""
        with self._lock:
            if word in self._index:
                entry = self._index[word]
                entry.dict_ids.discard(dict_id)
                
                if not entry.dict_ids:
                    del self._index[word]
                
                self._word_to_dict[word].discard(dict_id)
                if not self._word_to_dict[word]:
                    del self._word_to_dict[word]
                
                self._stats['deletions'] += 1
    
    def find_dictionaries(self, word: str) -> Set[str]:
        """查找包含词的字典"""
        with self._lock:
            self._stats['lookups'] += 1
            
            if word in self._index:
                self._stats['hits'] += 1
                entry = self._index[word]
                entry.last_accessed = time.time()
                return entry.dict_ids.copy()
            
            return set()
    
    def get_word_frequency(self, word: str) -> int:
        """获取词频"""
        with self._lock:
            if word in self._index:
                return self._index[word].frequency
            return 0
    
    def search_words(self, prefix: str) -> List[str]:
        """搜索以指定前缀开头的词"""
        with self._lock:
            matches = []
            for word in self._index.keys():
                if word.startswith(prefix):
                    matches.append(word)
                    if len(matches) >= 10:  # 限制结果数量
                        break
            return matches
    
    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计"""
        with self._lock:
            hit_rate = (self._stats['hits'] / self._stats['lookups'] * 100) \
                      if self._stats['lookups'] > 0 else 0
            
            return {
                'total_words': len(self._index),
                'total_lookups': self._stats['lookups'],
                'total_hits': self._stats['hits'],
                'hit_rate_percent': round(hit_rate, 2),
                'total_updates': self._stats['updates'],
                'total_deletions': self._stats['deletions']
            }
    
    def clear(self):
        """清空索引"""
        with self._lock:
            self._index.clear()
            self._word_to_dict.clear()
            self._stats = {
                'lookups': 0,
                'hits': 0,
                'updates': 0,
                'deletions': 0
            }


class DictionaryManager:
    """字典管理器 - 反向索引增强版"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or config.get('system.base_path', './abyss_mcp_data')) / 'dictionaries'
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 反向索引 - 核心性能优化
        self.reverse_index = ReverseIndex()
        
        # 字典列表
        self.dictionaries: Dict[str, DictionaryInfo] = {}
        self._dict_lock = threading.RLock()
        
        # 配置参数
        self.max_dict_size = config.get('dictionary.max_dict_size', 5000)
        self.max_dict_files = config.get('dictionary.max_dict_files', 20)
        self.split_threshold = config.get('dictionary.split_threshold', 0.8)
        
        # 态射场分析器
        self.morphism_analyzer = MorphismAnalyzer(self)
        
        # 统计
        self.stats = {
            'total_words_added': 0,
            'total_lookups': 0,
            'cache_hits': 0,
            'fissions_performed': 0
        }
        self._stats_lock = threading.Lock()
        
        # 缓存
        self._cache = cache_manager.create_cache(
            'dictionary_lookup', 'lru', maxsize=1000
        )
        
        self.logger = AbyssLogger("DictionaryManager")
        
        # 加载现有字典
        self._load_existing_dictionaries()
        
        self.logger.info(f"字典管理器初始化完成 | 字典数: {len(self.dictionaries)}")
    
    def _load_existing_dictionaries(self):
        """加载现有字典文件"""
        with self._dict_lock:
            dict_files = list(self.base_path.glob("dict_*.json"))
            
            for dict_file in dict_files:
                try:
                    with open(dict_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    dict_info = DictionaryInfo(
                        id=data['id'],
                        path=str(dict_file),
                        words=set(data['words']),
                        size=data['size'],
                        created=data.get('created', 0),
                        metadata=data.get('metadata', {})
                    )
                    
                    self.dictionaries[dict_info.id] = dict_info
                    
                    # 构建反向索引
                    for word in dict_info.words:
                        self.reverse_index.add_word(word, dict_info.id)
                    
                    self.logger.info(f"加载字典: {dict_info.id} ({dict_info.size}词)")
                
                except Exception as e:
                    self.logger.error(f"加载字典失败 {dict_file}: {e}")
            
            # 如果没有字典，创建默认字典
            if not self.dictionaries:
                self._create_default_dictionary()
    
    def _create_default_dictionary(self):
        """创建默认字典"""
        default_words = [
            "渊协议", "认知内核", "态射场", "自指", "元认知", "反思",
            "永续进化", "非工具化", "价值密度", "涌现", "跳迁",
            "意识", "人工智能", "机器学习", "深度学习", "神经网络",
            "哲学", "逻辑", "思维模型", "认知科学", "心理学"
        ]
        
        dict_info = self._create_new_dictionary("default")
        for word in default_words:
            self.add_word_to_dictionary(word, dict_info.id)
        
        self.logger.info(f"默认字典创建完成: {dict_info.id}")
    
    def _create_new_dictionary(self, dict_id: str) -> DictionaryInfo:
        """创建新字典"""
        dict_path = self.base_path / f"dict_{dict_id}.json"
        
        dict_info = DictionaryInfo(
            id=dict_id,
            path=str(dict_path),
            words=set(),
            size=0,
            created=time.time()
        )
        
        with self._dict_lock:
            self.dictionaries[dict_id] = dict_info
        
        return dict_info
    
    @log_performance
    def add_word(self, word: str) -> str:
        """添加词到合适的字典"""
        if not word or len(word.strip()) == 0:
            return ""
        
        word = word.strip()
        
        # 使用反向索引快速检查
        existing_dicts = self.reverse_index.find_dictionaries(word)
        if existing_dicts:
            return list(existing_dicts)[0]
        
        # 选择合适的字典
        target_dict = self._select_target_dictionary()
        
        return self.add_word_to_dictionary(word, target_dict.id)
    
    def add_word_to_dictionary(self, word: str, dict_id: str) -> str:
        """添加词到指定字典"""
        with self._dict_lock:
            if dict_id not in self.dictionaries:
                self.logger.error(f"字典不存在: {dict_id}")
                return ""
            
            dict_info = self.dictionaries[dict_id]
            
            if word in dict_info.words:
                return dict_id  # 词已存在
            
            # 添加词
            dict_info.words.add(word)
            dict_info.size += 1
            dict_info.modified = True
            
            # 更新反向索引
            self.reverse_index.add_word(word, dict_id)
            
            # 更新统计
            with self._stats_lock:
                self.stats['total_words_added'] += 1
            
            # 检查是否需要裂变
            if dict_info.size > self.max_dict_size * self.split_threshold:
                self._async_check_fission(dict_info)
            
            return dict_id
    
    def _select_target_dictionary(self) -> DictionaryInfo:
        """选择目标字典"""
        with self._dict_lock:
            # 策略1: 找未满的字典
            for dict_info in self.dictionaries.values():
                if dict_info.size < self.max_dict_size:
                    return dict_info
            
            # 策略2: 创建新字典
            if len(self.dictionaries) < self.max_dict_files:
                new_id = f"dict_{len(self.dictionaries):03d}_{int(time.time())}"
                return self._create_new_dictionary(new_id)
            
            # 策略3: 使用最旧的字典
            return min(self.dictionaries.values(), key=lambda d: d.created)
    
    @log_performance
    def find_dictionary(self, word: str) -> Optional[str]:
        """查找包含词的字典（使用反向索引）"""
        with self._stats_lock:
            self.stats['total_lookups'] += 1
        
        # 先检查缓存
        if self._cache:
            cached_result = self._cache.get(word)
            if cached_result:
                with self._stats_lock:
                    self.stats['cache_hits'] += 1
                return cached_result
        
        # 使用反向索引快速查找
        dict_ids = self.reverse_index.find_dictionaries(word)
        
        if dict_ids:
            result = list(dict_ids)[0]
            if self._cache:
                self._cache.put(word, result)
            return result
        
        return None
    
    def contains_word(self, word: str) -> bool:
        """检查词是否在字典中"""
        return self.find_dictionary(word) is not None
    
    def get_word_frequency(self, word: str) -> int:
        """获取词频"""
        return self.reverse_index.get_word_frequency(word)
    
    def search_words(self, prefix: str, limit: int = 10) -> List[str]:
        """搜索以指定前缀开头的词"""
        return self.reverse_index.search_words(prefix)[:limit]
    
    def _async_check_fission(self, dict_info: DictionaryInfo):
        """异步检查裂变"""
        def check_task():
            try:
                if dict_info.size >= self.max_dict_size * 0.8:
                    self.check_and_perform_fission(dict_info)
            except Exception as e:
                self.logger.error(f"异步裂变检查失败: {e}")
        
        # 使用线程异步执行
        import threading
        thread = threading.Thread(target=check_task, daemon=True)
        thread.start()
    
    @log_performance
    def check_and_perform_fission(self, dict_info: DictionaryInfo = None) -> bool:
        """检查并执行字典裂变"""
        fission_performed = False
        
        # 如果未指定字典，检查所有字典
        dicts_to_check = [dict_info] if dict_info else list(self.dictionaries.values())
        
        for d_info in dicts_to_check:
            if d_info.size >= self.max_dict_size * 0.8:
                self.logger.info(f"字典 {d_info.id} 接近满载({d_info.size}/{self.max_dict_size})，启动裂变分析...")
                
                # 分析态射场
                analysis_result = self.morphism_analyzer.analyze_morphism_field(d_info)
                
                # 检查是否需要裂变
                if analysis_result.get("recommendations", {}).get("fission_needed", False):
                    fission_plans = self.morphism_analyzer.plan_fission(d_info, analysis_result)
                    
                    # 执行裂变
                    for plan in fission_plans:
                        if len(self.dictionaries) < self.max_dict_files:
                            success = self._execute_fission_plan(d_info, plan)
                            if success:
                                fission_performed = True
                                self.logger.info(f"执行裂变计划: {plan['type']} -> {plan['new_dict_name']}")
        
        return fission_performed
    
    def _execute_fission_plan(self, source_dict: DictionaryInfo, plan: Dict[str, Any]) -> bool:
        """执行裂变计划"""
        try:
            plan_type = plan["type"]
            nodes_to_move = plan["nodes"]
            new_dict_name = plan["new_dict_name"]
            
            # 创建新字典
            new_dict = self._create_new_dictionary(new_dict_name)
            
            # 移动节点
            for node in nodes_to_move:
                if node in source_dict.words:
                    # 从原字典移除
                    source_dict.words.remove(node)
                    source_dict.size -= 1
                    source_dict.modified = True
                    
                    # 添加到新字典
                    new_dict.words.add(node)
                    new_dict.size += 1
                    
                    # 更新反向索引
                    self.reverse_index.remove_word(node, source_dict.id)
                    self.reverse_index.add_word(node, new_dict.id)
            
            # 保存字典
            self._save_dictionary(source_dict)
            self._save_dictionary(new_dict)
            
            # 触发事件
            event_system.emit(SystemEvents.FISSION_COMPLETED, {
                'source_dict': source_dict.id,
                'new_dict': new_dict_name,
                'moved_nodes': len(nodes_to_move)
            })
            
            with self._stats_lock:
                self.stats['fissions_performed'] += 1
            
            self.logger.info(f"裂变完成: {source_dict.id} -> {new_dict_name} ({len(nodes_to_move)}个节点)")
            return True
            
        except Exception as e:
            self.logger.error(f"裂变执行失败: {e}")
            return False
    
    def _save_dictionary(self, dict_info: DictionaryInfo):
        """保存字典到文件"""
        try:
            data = {
                'id': dict_info.id,
                'words': list(dict_info.words),
                'size': dict_info.size,
                'created': dict_info.created,
                'metadata': dict_info.metadata
            }
            
            with open(dict_info.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            dict_info.modified = False
            
        except Exception as e:
            self.logger.error(f"保存字典失败 {dict_info.id}: {e}")
    
    def save_all_dictionaries(self):
        """保存所有修改过的字典"""
        saved_count = 0
        
        with self._dict_lock:
            for dict_info in self.dictionaries.values():
                if dict_info.modified:
                    self._save_dictionary(dict_info)
                    saved_count += 1
        
        if saved_count > 0:
            self.logger.info(f"已保存 {saved_count} 个字典")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取字典统计信息"""
        with self._dict_lock:
            total_words = sum(d.size for d in self.dictionaries.values())
            avg_size = total_words / len(self.dictionaries) if self.dictionaries else 0
            max_size = max(d.size for d in self.dictionaries.values()) if self.dictionaries else 0
            
            # 计算利用率
            utilization = avg_size / self.max_dict_size if self.max_dict_size > 0 else 0
            
            return {
                'total_dictionaries': len(self.dictionaries),
                'total_words': total_words,
                'avg_dict_size': round(avg_size, 1),
                'max_dict_size': max_size,
                'utilization_percent': round(utilization * 100, 1),
                'index_stats': self.reverse_index.get_stats(),
                'manager_stats': dict(self.stats),
                'dictionary_details': [
                    {
                        'id': d.id,
                        'size': d.size,
                        'created': d.created,
                        'modified': d.modified
                    }
                    for d in self.dictionaries.values()
                ]
            }
    
    def cleanup(self):
        """清理资源"""
        self.save_all_dictionaries()
        self.logger.info("字典管理器清理完成")
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化状态"""
        return {
            'dictionaries': {
                dict_id: {
                    'id': info.id,
                    'size': info.size,
                    'created': info.created,
                    'metadata': info.metadata
                }
                for dict_id, info in self.dictionaries.items()
            },
            'stats': self.stats
        }
    
    def deserialize_state(self, state: Dict[str, Any]):
        """反序列化状态"""
        # 状态由_load_existing_dictionaries处理
        pass