#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议 v5.0 - 默认模式网络 (DMN - Default Mode Network)
模拟人类大脑的DMN功能：内省、自我反思、记忆整理、未来预测

功能特性：
✅ 内省循环：定期自我反思
✅ 记忆整理：自动整合和重组记忆
✅ 模式发现：在无任务时发现隐藏模式
✅ 预测模拟：基于现有知识进行推演
✅ 创意生成：产生新的概念连接

作者: AbyssAC Protocol Team
版本: 5.0 (DMN Module)
"""

import os
import json
import time
import threading
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from enum import Enum

from core import logger, config, metrics, Result
from memory import MemorySystem, MemoryIntegrator


class DMNNode:
    """DMN节点：表示一个内省单元"""
    
    def __init__(self, node_id: str, node_type: str, content: Any, activation_level: float = 0.0):
        self.id = node_id
        self.type = node_type  # 'memory', 'concept', 'pattern', 'prediction'
        self.content = content
        self.activation_level = activation_level
        self.last_activated = None
        self.activation_count = 0
        self.connections = []  # 连接的节点ID
    
    def activate(self, intensity: float = 1.0):
        """激活节点"""
        self.activation_level = min(1.0, self.activation_level + intensity * 0.1)
        self.activation_count += 1
        self.last_activated = datetime.now().isoformat()
    
    def decay(self, factor: float = 0.95):
        """衰减激活水平"""
        self.activation_level *= factor
        return self.activation_level
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'activation_level': self.activation_level,
            'last_activated': self.last_activated,
            'activation_count': self.activation_count,
            'connections': self.connections
        }


class DMNNetwork:
    """DMN网络：管理内省节点和连接"""
    
    def __init__(self):
        self.nodes = {}  # node_id -> DMNNode
        self.connections = defaultdict(list)  # 节点间连接
        self.activation_history = deque(maxlen=100)
        self.network_lock = threading.RLock()
        
        # 网络参数
        self.decay_rate = 0.95
        self.spontaneous_activation_prob = 0.01
        self.max_nodes = 200
        
        logger.info("DMN网络初始化完成")
    
    def add_node(self, node: DMNNode) -> Result:
        """添加节点到网络"""
        try:
            with self.network_lock:
                if len(self.nodes) >= self.max_nodes:
                    # 移除最不活跃的节点
                    self._cleanup_inactive_nodes()
                
                self.nodes[node.id] = node
                logger.debug(f"DMN添加节点: {node.id} ({node.type})")
                return Result.ok(node.id)
        except Exception as e:
            return Result.error(f"添加DMN节点失败: {e}")
    
    def add_connection(self, node1_id: str, node2_id: str, strength: float = 1.0):
        """添加节点间连接"""
        with self.network_lock:
            if node1_id in self.nodes and node2_id in self.nodes:
                self.connections[node1_id].append({'target': node2_id, 'strength': strength})
                self.connections[node2_id].append({'target': node1_id, 'strength': strength})
                
                # 更新节点的连接列表
                if node2_id not in self.nodes[node1_id].connections:
                    self.nodes[node1_id].connections.append(node2_id)
                if node1_id not in self.nodes[node2_id].connections:
                    self.nodes[node2_id].connections.append(node1_id)
    
    def activate_node(self, node_id: str, intensity: float = 1.0) -> Result:
        """激活指定节点"""
        try:
            with self.network_lock:
                if node_id in self.nodes:
                    node = self.nodes[node_id]
                    node.activate(intensity)
                    
                    # 传播激活到连接的节点
                    self._propagate_activation(node_id, intensity * 0.3)
                    
                    # 记录历史
                    self.activation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'node_id': node_id,
                        'intensity': intensity
                    })
                    
                    return Result.ok(node.activation_level)
                else:
                    return Result.error(f"节点不存在: {node_id}")
        except Exception as e:
            return Result.error(f"激活节点失败: {e}")
    
    def spontaneous_activation(self):
        """自发激活（模拟DMN的自发活动）"""
        with self.network_lock:
            # 随机选择节点进行自发激活
            for node_id in list(self.nodes.keys()):
                if random.random() < self.spontaneous_activation_prob:
                    self.activate_node(node_id, intensity=0.3)
    
    def propagate_thought(self, seed_concept: str) -> List[str]:
        """思想传播：从一个概念开始，沿着连接传播"""
        activated_nodes = []
        visited = set()
        
        # 找到种子节点
        seed_node = None
        with self.network_lock:
            for node_id, node in self.nodes.items():
                if isinstance(node.content, str) and seed_concept in node.content:
                    seed_node = node_id
                    break
                elif isinstance(node.content, dict) and seed_concept in str(node.content):
                    seed_node = node_id
                    break
        
        if not seed_node:
            return activated_nodes
        
        # BFS传播
        queue = [seed_node]
        visited.add(seed_node)
        
        while queue and len(activated_nodes) < 10:  # 限制传播深度
            current = queue.pop(0)
            activated_nodes.append(current)
            
            # 激活当前节点
            self.activate_node(current, 0.5)
            
            # 添加到队列
            if current in self.connections:
                for conn in self.connections[current]:
                    if conn['target'] not in visited and conn['strength'] > 0.3:
                        visited.add(conn['target'])
                        queue.append(conn['target'])
        
        return activated_nodes
    
    def get_active_nodes(self, threshold: float = 0.1) -> List[DMNNode]:
        """获取活跃节点"""
        with self.network_lock:
            return [node for node in self.nodes.values() if node.activation_level > threshold]
    
    def decay_all(self):
        """所有节点衰减"""
        with self.network_lock:
            for node in self.nodes.values():
                node.decay(self.decay_rate)
    
    def _propagate_activation(self, node_id: str, intensity: float):
        """传播激活"""
        if node_id in self.connections:
            for conn in self.connections[node_id]:
                if conn['target'] in self.nodes:
                    target_node = self.nodes[conn['target']]
                    propagation_intensity = intensity * conn['strength']
                    if propagation_intensity > 0.05:  # 阈值
                        target_node.activate(propagation_intensity)
    
    def _cleanup_inactive_nodes(self):
        """清理不活跃的节点"""
        # 按激活水平排序，移除最低的10%
        sorted_nodes = sorted(self.nodes.items(), key=lambda x: x[1].activation_level)
        remove_count = max(1, len(sorted_nodes) // 10)
        
        for i in range(remove_count):
            node_id = sorted_nodes[i][0]
            del self.nodes[node_id]
            # 清理连接
            if node_id in self.connections:
                del self.connections[node_id]
            for conn_list in self.connections.values():
                conn_list[:] = [conn for conn in conn_list if conn['target'] != node_id]
    
    def serialize(self) -> Dict:
        """序列化网络状态"""
        with self.network_lock:
            return {
                'nodes': {node_id: node.to_dict() for node_id, node in self.nodes.items()},
                'activation_history': list(self.activation_history),
                'stats': {
                    'total_nodes': len(self.nodes),
                    'total_connections': sum(len(conns) for conns in self.connections.values()),
                    'active_nodes': len(self.get_active_nodes(0.1))
                }
            }
    
    def deserialize(self, data: Dict):
        """反序列化网络状态"""
        with self.network_lock:
            if 'nodes' in data:
                self.nodes.clear()
                for node_id, node_data in data['nodes'].items():
                    node = DMNNode(
                        node_id=node_data['id'],
                        node_type=node_data['type'],
                        content=node_data['content'],
                        activation_level=node_data.get('activation_level', 0.0)
                    )
                    node.activation_count = node_data.get('activation_count', 0)
                    node.last_activated = node_data.get('last_activated')
                    node.connections = node_data.get('connections', [])
                    self.nodes[node_id] = node
            
            if 'activation_history' in data:
                self.activation_history = deque(data['activation_history'], maxlen=100)


class DMNMode(Enum):
    """DMN运行模式"""
    RESTING = "resting"  # 静息态 - 自发思考
    INTEGRATION = "integration"  # 整合模式 - 主动整理记忆
    REFLECTION = "reflection"  # 反思模式 - 深度自省
    PREDICTION = "prediction"  # 预测模式 - 未来推演
    CREATIVE = "creative"  # 创意模式 - 概念重组


class DefaultModeNetwork:
    """
    默认模式网络 - 模拟人类大脑的DMN功能
    
    主要功能：
    1. 在无外部任务时进行自发思考
    2. 整合和重组记忆
    3. 发现隐藏的模式和关联
    4. 进行未来预测和规划
    5. 生成创意和新的概念连接
    """
    
    def __init__(self, memory_system: MemorySystem, ollama_client=None):
        self.memory = memory_system
        self.ollama = ollama_client
        self.network = DMNNetwork()
        
        # DMN状态
        self.current_mode = DMNMode.RESTING
        self.is_active = False
        self.last_activity = datetime.now()
        self.activity_count = 0
        
        # 配置参数
        self.dmn_config = config.get('dmn', {})
        self.idle_threshold = self.dmn_config.get('idle_threshold_seconds', 300)  # 5分钟无活动触发
        self.integration_interval = self.dmn_config.get('integration_interval', 1800)  # 30分钟
        self.reflection_depth = self.dmn_config.get('reflection_depth', 3)
        
        # 统计数据
        self.stats = {
            'total_activations': 0,
            'integrations_performed': 0,
            'patterns_discovered': 0,
            'predictions_made': 0
        }
        
        self.stats_lock = threading.RLock()
        
        logger.info("DMN默认模式网络初始化完成")
    
    def start(self):
        """启动DMN后台线程"""
        if self.is_active:
            return
        
        self.is_active = True
        
        # 启动DMN主循环
        self.dmn_thread = threading.Thread(target=self._dmn_main_loop, daemon=True, name="DMNMain")
        self.dmn_thread.start()
        
        logger.info("DMN默认模式网络已启动")
    
    def stop(self):
        """停止DMN"""
        self.is_active = False
        if hasattr(self, 'dmn_thread'):
            self.dmn_thread.join(timeout=5)
        logger.info("DMN默认模式网络已停止")
    
    def trigger_activity(self, activity_type: str = "manual"):
        """触发DMN活动"""
        self.last_activity = datetime.now()
        self.activity_count += 1
        
        with self.stats_lock:
            self.stats['total_activations'] += 1
        
        logger.debug(f"DMN活动触发: {activity_type}")
    
    def get_suggested_actions(self) -> List[Dict[str, Any]]:
        """获取DMN建议的行动"""
        suggestions = []
        
        # 基于当前网络状态生成建议
        active_nodes = self.network.get_active_nodes(0.2)
        
        if len(active_nodes) > 5:
            suggestions.append({
                'type': 'integration',
                'priority': 'high',
                'description': f'检测到{len(active_nodes)}个活跃概念节点，建议进行记忆整合',
                'action': 'perform_integration'
            })
        
        # 检查是否需要反思
        if self.activity_count > 10:
            suggestions.append({
                'type': 'reflection',
                'priority': 'medium',
                'description': '积累了足够的交互经验，建议进行深度反思',
                'action': 'perform_reflection'
            })
        
        return suggestions
    
    def _dmn_main_loop(self):
        """DMN主循环"""
        while self.is_active:
            try:
                # 检查是否应该进行DMN活动
                if self._should_be_active():
                    self._perform_dmn_cycle()
                
                # 等待下一个周期
                time.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"DMN主循环错误: {e}")
                time.sleep(60)  # 出错后等待更长时间
    
    def _should_be_active(self) -> bool:
        """判断DMN是否应该激活"""
        # 检查空闲时间
        idle_time = (datetime.now() - self.last_activity).total_seconds()
        
        # 如果超过阈值时间无外部活动，激活DMN
        return idle_time > self.idle_threshold
    
    def _perform_dmn_cycle(self):
        """执行一个DMN周期"""
        try:
            with metrics.timer('dmn_cycle'):
                # 1. 更新网络状态
                self.network.decay_all()
                self.network.spontaneous_activation()
                
                # 2. 根据模式执行不同活动
                if self.current_mode == DMNMode.INTEGRATION:
                    self._perform_memory_integration()
                elif self.current_mode == DMNMode.REFLECTION:
                    self._perform_reflection()
                elif self.current_mode == DMNMode.PREDICTION:
                    self._perform_prediction()
                elif self.current_mode == DMNMode.CREATIVE:
                    self._perform_creative_synthesis()
                else:  # RESTING
                    self._perform_resting_thoughts()
                
                # 3. 轮换模式
                self._rotate_mode()
                
        except Exception as e:
            logger.error(f"DMN周期执行失败: {e}")
    
    def _perform_memory_integration(self):
        """执行记忆整合"""
        try:
            # 使用记忆整合器进行智能整合
            if hasattr(self.memory, 'integrator'):
                result = self.memory.integrator.find_integration_candidates(min_relationships=3)
                
                if result and len(result) > 0:
                    # 选择最有潜力的整合候选
                    best_candidate = max(result, key=len)
                    
                    # 执行整合
                    integration_result = self.memory.integrator.integrate_memories(
                        best_candidate, self.ollama)
                    
                    if integration_result and integration_result.is_ok():
                        integration_data = integration_result.unwrap()
                        
                        # 添加到DMN网络
                        node = DMNNode(
                            node_id=f"int_{int(time.time())}",
                            node_type='pattern',
                            content={
                                'type': 'memory_integration',
                                'source_count': len(best_candidate),
                                'keywords': integration_data.get('keywords', [])
                            }
                        )
                        self.network.add_node(node)
                        
                        with self.stats_lock:
                            self.stats['integrations_performed'] += 1
                        
                        logger.info(f"DMN执行记忆整合: {len(best_candidate)} -> {integration_data.get('integration_id')}")
        except Exception as e:
            logger.warning(f"DMN记忆整合失败: {e}")
    
    def _perform_reflection(self):
        """执行深度反思"""
        try:
            # 获取最近的记忆和激活历史
            recent_memories = []
            for layer_id in [2, 3]:  # 分类记忆和工作记忆
                if layer_id in self.memory.layers:
                    memory_ids = self.memory.layers[layer_id]['memory_ids'][-10:]
                    for memory_id in memory_ids:
                        content_result = self.memory.get_memory_content(memory_id)
                        if content_result.is_ok():
                            recent_memories.append({
                                'id': memory_id,
                                'content': content_result.unwrap()
                            })
            
            if recent_memories and self.ollama and self.ollama.available:
                # 构建反思prompt
                memory_text = "\n".join([
                    f"- {mem['content'][:100]}" for mem in recent_memories[:5]
                ])
                
                prompt = f"""基于以下最近的记忆，进行深度反思：

{memory_text}

请分析：
1. 这些记忆之间的深层联系是什么？
2. 从中可以得出什么洞察？
3. 有什么需要改进的地方？

请用简洁的语言回答。"""
                
                reflection = self.ollama.generate(prompt, max_tokens=300)
                
                # 添加反思结果到DMN网络
                node = DMNNode(
                    node_id=f"ref_{int(time.time())}",
                    node_type='concept',
                    content={
                        'type': 'reflection',
                        'content': reflection,
                        'source_memories': [mem['id'] for mem in recent_memories[:5]]
                    }
                )
                self.network.add_node(node)
                
                logger.info(f"DMN生成反思: {reflection[:100]}...")
                
        except Exception as e:
            logger.warning(f"DMN反思失败: {e}")
    
    def _perform_prediction(self):
        """执行未来预测"""
        try:
            # 基于当前趋势进行预测
            active_nodes = self.network.get_active_nodes(0.3)
            
            if len(active_nodes) >= 3 and self.ollama and self.ollama.available:
                # 构建预测prompt
                concepts = [str(node.content)[:50] for node in active_nodes[:5]]
                concept_text = "\n".join([f"- {concept}" for concept in concepts])
                
                prompt = f"""基于以下活跃的概念，预测可能的发展趋势：

{concept_text}

请预测：
1. 这些概念会如何演化？
2. 可能出现什么新的关联？
3. 有什么潜在的机会或风险？

请用简洁的语言回答。"""
                
                prediction = self.ollama.generate(prompt, max_tokens=300)
                
                # 添加预测结果到DMN网络
                node = DMNNode(
                    node_id=f"pred_{int(time.time())}",
                    node_type='prediction',
                    content={
                        'type': 'prediction',
                        'content': prediction,
                        'based_on': concepts
                    }
                )
                self.network.add_node(node)
                
                with self.stats_lock:
                    self.stats['predictions_made'] += 1
                
                logger.info(f"DMN生成预测: {prediction[:100]}...")
                
        except Exception as e:
            logger.warning(f"DMN预测失败: {e}")
    
    def _perform_creative_synthesis(self):
        """执行创意合成"""
        try:
            # 寻找不相关的概念进行连接
            active_nodes = self.network.get_active_nodes(0.2)
            
            if len(active_nodes) >= 4:
                # 选择两个激活水平相似但不直接相关的节点
                node_list = list(active_nodes)
                random.shuffle(node_list)
                
                node_a = node_list[0]
                node_b = node_list[1]
                
                # 检查是否已连接
                if node_b.id not in node_a.connections:
                    # 建立新连接
                    self.network.add_connection(node_a.id, node_b.id, strength=0.5)
                    
                    # 如果有Ollama，生成创意
                    if self.ollama and self.ollama.available:
                        content_a = str(node_a.content)[:100]
                        content_b = str(node_b.content)[:100]
                        
                        prompt = f"""将以下两个概念进行创意连接：

概念1: {content_a}
概念2: {content_b}

请生成：
1. 这两个概念的关联点
2. 可能产生的新想法或应用
3. 一个具体的例子

请用简洁的语言回答。"""
                        
                        creative_idea = self.ollama.generate(prompt, max_tokens=300)
                        
                        # 添加创意到DMN网络
                        node = DMNNode(
                            node_id=f"creat_{int(time.time())}",
                            node_type='concept',
                            content={
                                'type': 'creative_synthesis',
                                'idea': creative_idea,
                                'sources': [node_a.id, node_b.id]
                            }
                        )
                        self.network.add_node(node)
                        
                        with self.stats_lock:
                            self.stats['patterns_discovered'] += 1
                        
                        logger.info(f"DMN生成创意: {creative_idea[:100]}...")
                        
        except Exception as e:
            logger.warning(f"DMN创意合成失败: {e}")
    
    def _perform_resting_thoughts(self):
        """执行静息态思考"""
        # 随机选择一些记忆进行回顾
        try:
            # 从各层随机选择记忆
            all_memories = []
            for layer_id in [1, 2, 3]:  # 不包括元认知层
                if layer_id in self.memory.layers:
                    memory_ids = self.memory.layers[layer_id]['memory_ids']
                    if memory_ids:
                        selected = random.sample(memory_ids, min(3, len(memory_ids)))
                        all_memories.extend(selected)
            
            # 随机激活一些记忆的DMN节点
            for memory_id in all_memories[:2]:
                node_id = f"mem_{memory_id}"
                
                # 检查是否已有对应的DMN节点
                if node_id not in self.network.nodes:
                    content_result = self.memory.get_memory_content(memory_id)
                    if content_result.is_ok():
                        # 创建记忆节点
                        node = DMNNode(
                            node_id=node_id,
                            node_type='memory',
                            content=content_result.unwrap()[:200]
                        )
                        self.network.add_node(node)
                
                # 激活节点
                self.network.activate_node(node_id, intensity=0.2)
                
        except Exception as e:
            logger.debug(f"静息思考失败: {e}")
    
    def _rotate_mode(self):
        """轮换DMN模式"""
        modes = [DMNMode.INTEGRATION, DMNMode.REFLECTION, DMNMode.PREDICTION, DMNMode.CREATIVE]
        current_index = modes.index(self.current_mode) if self.current_mode in modes else -1
        
        if current_index >= 0:
            next_index = (current_index + 1) % len(modes)
            self.current_mode = modes[next_index]
        else:
            self.current_mode = DMNMode.INTEGRATION
    
    def get_state(self) -> Dict:
        """获取DMN状态"""
        with self.stats_lock:
            stats_copy = self.stats.copy()
        
        # 修复：确保current_mode是字符串
        current_mode_str = self.current_mode.value if hasattr(self.current_mode, 'value') else str(self.current_mode)
        
        return {
            'is_active': self.is_active,
            'current_mode': current_mode_str,
            'last_activity': self.last_activity.isoformat(),
            'activity_count': self.activity_count,
            'network_stats': self.network.serialize()['stats'],
            'stats': stats_copy
        }
        """获取DMN状态"""
        with self.stats_lock:
            stats_copy = self.stats.copy()
        
        return {
            'is_active': self.is_active,
            'current_mode': self.current_mode.value,
            'last_activity': self.last_activity.isoformat(),
            'activity_count': self.activity_count,
            'network_stats': self.network.serialize()['stats'],
            'stats': stats_copy
        }
    
    def serialize_state(self) -> Result:
        """序列化DMN状态"""
        try:
            return Result.ok({
                'network': self.network.serialize(),
                'current_mode': self.current_mode.value,
                'last_activity': self.last_activity.isoformat(),
                'activity_count': self.activity_count,
                'stats': self.stats
            })
        except Exception as e:
            return Result.error(f"序列化DMN失败: {e}")
    
    def deserialize_state(self, state: Dict):
        """反序列化DMN状态"""
        if 'network' in state:
            self.network.deserialize(state['network'])
        
        if 'current_mode' in state:
            try:
                self.current_mode = DMNMode(state['current_mode'])
            except:
                self.current_mode = DMNMode.RESTING
        
        if 'last_activity' in state:
            self.last_activity = datetime.fromisoformat(state['last_activity'])
        
        if 'activity_count' in state:
            self.activity_count = state['activity_count']
        
        if 'stats' in state:
            self.stats.update(state['stats'])


print("[✅] DMN默认模式网络模块实现完成")
print("    - 模拟人类大脑的自发思考")
print("    - 自动记忆整合和重组")
print("    - 模式发现和创意生成")
print("    - 预测和规划能力")
