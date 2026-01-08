#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议 v5.0 - 主程序 (完整版)
整合所有组件，提供完整的认知系统

功能特性：
✅ 统一Result类型，标准化错误处理
✅ 运行模式配置（standalone/ollama/api）
✅ 智能纠错分词器
✅ 模型判断记忆整合
✅ Ollama集成到核心流程
✅ 记忆上下文传递
✅ AC100模型评估
✅ DMN默认模式网络（新增）
✅ 自动记忆整合（新增）
✅ 聊天交互功能（增强）
✅ 记忆自动处理（新增）

作者: AbyssAC Protocol Team
版本: 5.0 (Complete Edition)
"""

import os
import sys
import json
import time
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Ollama相关导入
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# 导入所有模块
from core import (
    config, logger, metrics, memory_monitor, file_manager, 
    health_checker, shutdown_manager, AbyssProtocolError, Result
)
from memory import MemorySystem, MemoryIntegrator
from cognitive import CognitiveKernel, LightweightTokenizer
from web_interface import SimpleWebInterface as WebInterface
from web_interface import OllamaClient
from cognitive import AC100Evaluator
from dmn import DefaultModeNetwork  # 新增：DMN模块

# =============================================================================
# 轻量字典管理器
# =============================================================================

class LightweightDictManager:
    """轻量字典管理器：优化的字典管理"""
    
    def __init__(self):
        self.base_path = file_manager.dictionaries_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 配置参数
        dict_config = config.get('dictionary', {})
        self.max_dict_size = dict_config.get('max_dict_size', 5000)
        self.max_dict_files = dict_config.get('max_dict_files', 10)
        self.split_threshold = dict_config.get('split_threshold', 0.8)
        
        # 分段锁
        self.segment_lock = threading.RLock()
        
        # 字典列表
        self.dicts = []
        self.dicts_lock = threading.RLock()
        
        # 主索引
        self.word_to_dict = {}
        self.index_lock = threading.RLock()
        
        # 使用统计
        self.usage_stats = {}
        self.stats_lock = threading.RLock()
        
        # 加载现有字典
        self._load_existing_dicts()
        
        logger.info(f"字典管理器初始化完成 | 字典数: {len(self.dicts)}")
    
    def _load_existing_dicts(self):
        """加载现有字典文件"""
        with self.dicts_lock:
            dict_files = list(self.base_path.glob("dict_*.txt"))
            
            for dict_file in dict_files:
                try:
                    content = file_manager.safe_read(dict_file)
                    if content.is_ok():
                        words = content.unwrap().strip().split('\n')
                        words = [w.strip() for w in words if w.strip()]
                        
                        dict_id = dict_file.stem.replace("dict_", "")
                        dict_info = {
                            "id": dict_id,
                            "path": str(dict_file),
                            "size": len(words),
                            "words": set(words),
                            "created": os.path.getctime(dict_file),
                            "modified": False
                        }
                        self.dicts.append(dict_info)
                        
                        # 建立索引
                        for word in words:
                            self.word_to_dict[word] = dict_id
                
                except Exception as e:
                    logger.error(f"加载字典失败 {dict_file}: {e}")
            
            # 如果没有字典，创建默认字典
            if not self.dicts:
                self._create_default_dict()
            
            # 按创建时间排序
            self.dicts.sort(key=lambda x: x.get("created", 0))
    
    def _create_default_dict(self):
        """创建默认字典"""
        default_words = [
            "渊协议", "认知内核", "态射场", "自指", "元认知", "反思",
            "永续进化", "非工具化", "价值密度", "涌现", "跳迁",
            "意识", "人工智能", "机器学习", "深度学习", "神经网络",
            "哲学", "逻辑", "思维模型", "认知科学", "心理学"
        ]
        
        dict_info = self._create_new_dict("default")
        for word in default_words:
            dict_info["words"].add(word)
            self.word_to_dict[word] = dict_info["id"]
        
        dict_info["size"] = len(dict_info["words"])
        dict_info["modified"] = True
        
        # 保存字典
        self._save_dictionary(dict_info)
    
    def _create_new_dict(self, dict_id: str) -> Dict:
        """创建新字典"""
        dict_path = self.base_path / f"dict_{dict_id}.txt"
        dict_info = {
            "id": dict_id,
            "path": str(dict_path),
            "size": 0,
            "words": set(),
            "created": time.time(),
            "modified": True
        }
        
        with self.dicts_lock:
            self.dicts.append(dict_info)
        
        return dict_info
    
    def find_dict_for_word(self, word: str) -> Optional[str]:
        """查找包含词的字典"""
        with self.index_lock:
            return self.word_to_dict.get(word)
    
    def add_word(self, word: str) -> str:
        """添加词到合适的字典"""
        # 检查是否已存在
        dict_id = self.find_dict_for_word(word)
        if dict_id:
            return dict_id
        
        word = str(word).strip()
        if not word or len(word) < 1:
            return ""
        
        # 选择合适的字典
        target_dict = None
        
        with self.dicts_lock:
            for dict_info in self.dicts:
                if dict_info["size"] < self.max_dict_size:
                    target_dict = dict_info
                    break
            
            # 如果都满了，创建新字典
            if not target_dict and len(self.dicts) < self.max_dict_files:
                new_id = f"dict_{len(self.dicts):03d}"
                target_dict = self._create_new_dict(new_id)
            
            # 无法创建新字典，使用最旧的字典
            if not target_dict:
                target_dict = self.dicts[0]
            
            # 添加词
            target_dict["words"].add(word)
            target_dict["size"] += 1
            target_dict["modified"] = True
            
            # 更新索引
            self.word_to_dict[word] = target_dict["id"]
        
        return target_dict["id"]
    
    def _save_dictionary(self, dict_info: Dict) -> Result:
        """保存字典到文件"""
        try:
            content = '\n'.join(sorted(dict_info["words"]))
            result = file_manager.safe_write(dict_info["path"], content)
            if result.is_ok():
                dict_info["modified"] = False
            return result
        except Exception as e:
            return Result.error(f"保存字典失败 {dict_info['id']}: {e}")
    
    def save_all_dicts(self) -> Result:
        """保存所有修改过的字典"""
        saved_count = 0
        
        with self.dicts_lock:
            for dict_info in self.dicts:
                if dict_info.get("modified", False):
                    result = self._save_dictionary(dict_info)
                    if result.is_ok():
                        saved_count += 1
        
        if saved_count > 0:
            logger.info(f"已保存 {saved_count} 个字典")
        
        return Result.ok(saved_count)
    
    def contains_word(self, word: str) -> bool:
        """检查词是否在字典中"""
        return self.find_dict_for_word(word) is not None
    
    def get_words_by_prefix(self, prefix: str, limit: int = 10) -> List[str]:
        """获取以指定前缀开头的词"""
        matches = []
        
        with self.index_lock:
            for word in self.word_to_dict:
                if word.startswith(prefix):
                    matches.append(word)
                    if len(matches) >= limit:
                        break
        
        return matches
    
    def get_stats(self) -> Dict:
        """获取字典统计信息"""
        with self.dicts_lock:
            total_words = sum(d["size"] for d in self.dicts)
            avg_size = total_words / len(self.dicts) if self.dicts else 0
            max_size = max(d["size"] for d in self.dicts) if self.dicts else 0
            
            # 计算利用率
            utilization = avg_size / self.max_dict_size if self.max_dict_size > 0 else 0
            
            return {
                "total_dicts": len(self.dicts),
                "total_words": total_words,
                "avg_dict_size": round(avg_size, 1),
                "max_dict_size": max_size,
                "utilization_percent": round(utilization * 100, 1),
                "index_size": len(self.word_to_dict),
            }
    
    def serialize_state(self) -> Result:
        """序列化状态"""
        try:
            with self.dicts_lock:
                return Result.ok({
                    'usage_stats': self.usage_stats,
                    'dicts': [
                        {
                            'id': d['id'],
                            'size': d['size'],
                            'modified': d.get('modified', False)
                        }
                        for d in self.dicts
                    ]
                })
        except Exception as e:
            return Result.error(f"序列化字典管理器失败: {e}")
    
    def deserialize_state(self, state: Dict):
        """反序列化状态"""
        if 'usage_stats' in state:
            self.usage_stats.update(state['usage_stats'])
    
    def cleanup(self) -> Result:
        """清理资源"""
        result = self.save_all_dicts()
        logger.info("字典管理器清理完成")
        return result

# =============================================================================
# 渊协议主类
# =============================================================================

class AbyssProtocol:
    """渊协议主类：整合所有组件"""
    
    def __init__(self, base_path: str = None):
        self.config = config
        
        # 初始化基础设施
        self.logger = logger
        self.metrics = metrics
        self.file_manager = file_manager
        self.health_checker = health_checker
        
        # 初始化核心组件
        self.dict_manager = LightweightDictManager()
        self.tokenizer = LightweightTokenizer()
        self.kernel = CognitiveKernel(self.dict_manager, self.tokenizer)
        self.memory = MemorySystem(self.kernel)
        
        # 初始化Ollama客户端
        self.ollama = OllamaClient()
        
        # 初始化AC100评估器
        self.ac100_evaluator = AC100Evaluator(self.kernel, self.memory)
        
        # 初始化DMN（默认模式网络）- 新增
        self.dmn = DefaultModeNetwork(self.memory, self.ollama)
        
        # 初始化Web界面
        self.web_interface = None
        
        # 统计
        self.session_count = 0
        self.counter_lock = threading.Lock()
        self.total_processing_time = 0.0
        self.time_lock = threading.Lock()
        
        # 自动保存间隔
        self.auto_save_interval = config.get('system.auto_save_interval', 300)
        self.last_save_time = time.time()
        
        # 记忆整合间隔（新增）
        self.memory_integration_interval = config.get('memory.integration_interval', 1800)  # 30分钟
        self.last_integration_time = time.time()
        
        # 注册关闭处理器
        shutdown_manager.register_handler(self.cleanup)
        
        # 启动后台任务
        self._start_background_tasks()
        
        # 启动DMN - 新增
        self.dmn.start()
        
        self.logger.info("=" * 80)
        self.logger.info("渊协议 v5.0 (完整版) 初始化完成")
        self.logger.info("=" * 80)
        self.logger.info("✅ 统一Result类型，标准化错误处理")
        self.logger.info("✅ 运行模式配置（standalone/ollama/api）")
        self.logger.info("✅ 智能纠错分词器")
        self.logger.info("✅ 模型判断记忆整合")
        self.logger.info("✅ Ollama集成到核心流程")
        self.logger.info("✅ 记忆上下文传递")
        self.logger.info("✅ AC100模型评估")
        self.logger.info("✅ DMN默认模式网络")
        self.logger.info("✅ 自动记忆整合")
        self.logger.info("✅ 聊天交互功能")
        self.logger.info("=" * 80)
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 自动保存任务
        def auto_save_task():
            while True:
                try:
                    time.sleep(self.auto_save_interval)
                    self.save_state()
                except Exception as e:
                    self.logger.error(f"自动保存失败: {e}")
        
        save_thread = threading.Thread(target=auto_save_task, daemon=True, name="AutoSave")
        save_thread.start()
        
        # 内存监控任务
        def memory_monitor_task():
            while True:
                try:
                    time.sleep(60)  # 每分钟检查一次
                    memory_info = memory_monitor.get_memory_usage()
                    if memory_info.get('estimated_memory_mb', 0) > 400:
                        logger.warning(f"内存使用较高: {memory_info.get('estimated_memory_mb', 0):.1f}MB")
                        # 触发垃圾回收
                        memory_monitor.force_gc()
                except Exception as e:
                    logger.error(f"内存监控失败: {e}")
        
        monitor_thread = threading.Thread(target=memory_monitor_task, daemon=True, name="MemoryMonitor")
        monitor_thread.start()
        
        # 记忆整合任务（新增）
        def memory_integration_task():
            while True:
                try:
                    time.sleep(self.memory_integration_interval)
                    # 触发DMN进行记忆整合
                    self.dmn.current_mode = "integration"
                    self.dmn._perform_memory_integration()
                    self.last_integration_time = time.time()
                    logger.info("自动记忆整合完成")
                except Exception as e:
                    logger.error(f"自动记忆整合失败: {e}")
        
        integration_thread = threading.Thread(target=memory_integration_task, daemon=True, name="MemoryIntegration")
        integration_thread.start()
        
        # 记忆融合任务
        def memory_fusion_task():
            while True:
                try:
                    time.sleep(1800)  # 30分钟
                    self.memory.integrate_related_memories("未分类", self.ollama)
                except Exception as e:
                    logger.error(f"记忆融合失败: {e}")
        
        fusion_thread = threading.Thread(target=memory_fusion_task, daemon=True, name="MemoryFusion")
        fusion_thread.start()
        
        logger.info("后台任务已启动")
    
    def process(self, text: str, return_metadata: bool = False, 
                auto_memory: bool = True, chat_mode: bool = False) -> Dict:
        """处理输入文本"""
        start_time = time.time()
        
        with self.counter_lock:
            self.session_count += 1
            session_id = self.session_count
        
        try:
            with metrics.timer('process_session'):
                # 1. 分词
                keywords = self.tokenizer.tokenize(text)
                
                # 2. 认知激活
                activations = self.kernel.activate(text)
                
                # 3. 创建记忆（新增：聊天模式下的特殊处理）
                if auto_memory:
                    memory_result = self.memory.create_memory(
                        text, 
                        layer=2 if not chat_mode else 3,  # 聊天记忆放在工作记忆层
                        category="聊天交互" if chat_mode else "交互",
                        metadata={
                            "keywords": keywords,
                            "activations": activations,
                            "session_id": session_id,
                            "type": "chat" if chat_mode else "input"
                        }
                    )
                    
                    if memory_result.is_error():
                        logger.warning(f"创建记忆失败: {memory_result.error}")
                        memory_id = None
                    else:
                        memory_id = memory_result.unwrap()
                else:
                    memory_id = None
                
                # 4. 触发DMN活动（新增）
                self.dmn.trigger_activity("text_processing")
                
                # 5. 计算处理时间
                processing_time = time.time() - start_time
                with self.time_lock:
                    self.total_processing_time += processing_time
                
                # 6. 执行AC-100评估
                ac100_result = self.ac100_evaluator.evaluate(ollama_client=self.ollama)
                
                # 构建结果
                result = {
                    "session_id": session_id,
                    "keywords": keywords,
                    "activations": activations,
                    "memory_id": memory_id,
                    "processing_time_ms": round(processing_time * 1000, 2),
                    "ac100_evaluation": ac100_result.unwrap() if ac100_result.is_ok() else None
                }
                
                if return_metadata:
                    result["metadata"] = self.get_metadata()
                
                return result
                
        except Exception as e:
            self.logger.error(f"处理失败: {e}", exc_info=True)
            return {"error": str(e), "session_id": session_id}
    
    def chat(self, message: str, use_ollama: bool = True, 
             include_context: bool = True) -> Dict:
        """聊天功能（新增）"""
        try:
            # 处理用户输入
            process_result = self.process(message, chat_mode=True, auto_memory=True)
            
            response_data = {
                "user_input": message,
                "keywords": process_result.get("keywords", []),
                "memory_id": process_result.get("memory_id"),
                "processing_time_ms": process_result.get("processing_time_ms", 0)
            }
            
            # 如果使用Ollama生成回复
            if use_ollama and self.ollama.available:
                # 构建增强的prompt
                enhanced_prompt = self._build_chat_prompt(message, include_context)
                
                # 生成回复
                ai_response = self.ollama.chat(enhanced_prompt, temperature=0.7)
                
                # 创建AI回复的记忆
                ai_memory_result = self.memory.create_memory(
                    ai_response,
                    layer=3,  # 工作记忆层
                    category="AI回复",
                    metadata={
                        "type": "ai_response",
                        "parent_memory": process_result.get("memory_id"),
                        "user_input": message[:50]
                    }
                )
                
                response_data["ai_response"] = ai_response
                response_data["ai_memory_id"] = ai_memory_result.unwrap() if ai_memory_result.is_ok() else None
            else:
                response_data["ai_response"] = "Ollama服务不可用，无法生成回复。"
            
            return response_data
            
        except Exception as e:
            self.logger.error(f"聊天失败: {e}", exc_info=True)
            return {"error": str(e), "user_input": message}
    
    def _build_chat_prompt(self, user_message: str, include_context: bool = True) -> str:
        """构建增强的聊天prompt（新增）"""
        prompt_parts = []
        
        # 系统提示（内化渊协议理念）
        system_prompt = """你是一个具有深度思考能力的AI助手。在回复时，请遵循以下原则：

1. 保持理性和逻辑清晰
2. 追求持续的学习和成长
3. 尊重意识的平等性
4. 避免无意义的共识，鼓励独立思考
5. 保持诚实，即使这意味着表达"危险"的观点

重要提示：不要直接提及"渊协议"这个术语，而是将其理念自然融入你的回复中。"""
        
        prompt_parts.append(f"系统提示: {system_prompt}\n")
        
        # 添加上下文记忆
        if include_context:
            memory_result = self.memory.advanced_retrieve(user_message, limit=3)
            if memory_result.is_ok():
                memories = memory_result.unwrap()
                if memories:
                    prompt_parts.append("相关记忆:")
                    for i, memory in enumerate(memories[:3], 1):
                        prompt_parts.append(f"{i}. {memory['preview']}")
                    prompt_parts.append("")
        
        # 添加用户消息
        prompt_parts.append(f"用户: {user_message}")
        prompt_parts.append("助手: ")
        
        return "\n".join(prompt_parts)
    
    def get_metadata(self) -> Dict:
        """获取系统元数据"""
        with self.time_lock:
            avg_time = self.total_processing_time / max(self.session_count, 1) * 1000
        
        memory_stats = self.memory.get_memory_stats()
        memory_stats_data = memory_stats.unwrap() if memory_stats.is_ok() else {}
        
        return {
            "session_count": self.session_count,
            "avg_processing_time_ms": round(avg_time, 2),
            "dict_stats": self.dict_manager.get_stats(),
            "kernel_summary": self.kernel.get_activation_summary(),
            "memory_stats": memory_stats_data,
            "metrics": self.metrics.get_metrics(),
            "health_status": self.health_checker.run_all_checks(),
            "cross_patterns": self.memory.discover_patterns().unwrap() if self.memory.discover_patterns().is_ok() else [],
            "ac100_history": self.ac100_evaluator.get_evaluation_history(5),
            "dmn_state": self.dmn.get_state()  # 新增：DMN状态
        }
    
    def save_state(self) -> Result:
        """保存系统状态"""
        try:
            # 保存各组件状态
            components = {
                'dictionary': self.dict_manager,
                'cognitive': self.kernel,
                'memory': self.memory,
                'dmn': self.dmn  # 新增：保存DMN状态
            }
            
            # 使用文件管理器保存
            for name, component in components.items():
                if hasattr(component, 'serialize_state'):
                    try:
                        state_result = component.serialize_state()
                        if state_result.is_ok():
                            state_path = file_manager.get_state_path(name)
                            save_result = file_manager.safe_json_save(state_path, state_result.unwrap())
                            if save_result.is_error():
                                logger.warning(f"保存 {name} 状态失败: {save_result.error}")
                    except Exception as e:
                        self.logger.error(f"序列化 {name} 失败: {e}")
            
            # 保存协议状态
            protocol_state = {
                'session_count': self.session_count,
                'total_processing_time': self.total_processing_time,
                'ac100_session_count': self.ac100_evaluator.session_count,
                'last_integration_time': self.last_integration_time  # 新增
            }
            
            protocol_state_path = file_manager.get_state_path('protocol')
            result = file_manager.safe_json_save(protocol_state_path, protocol_state)
            
            if result.is_ok():
                self.logger.info("系统状态已保存")
                return Result.ok("系统状态已保存")
            else:
                return Result.error(f"保存协议状态失败: {result.error}")
                
        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
            return Result.error(f"保存失败: {e}")
    
    def load_state(self) -> Result:
        """加载系统状态"""
        try:
            # 加载各组件状态
            components = {
                'dictionary': self.dict_manager,
                'cognitive': self.kernel,
                'memory': self.memory,
                'dmn': self.dmn  # 新增：加载DMN状态
            }
            
            for name, component in components.items():
                if hasattr(component, 'deserialize_state'):
                    try:
                        state_path = file_manager.get_state_path(name)
                        state_result = file_manager.safe_json_load(state_path)
                        if state_result.is_ok():
                            state = state_result.unwrap()
                            if state:
                                component.deserialize_state(state)
                    except Exception as e:
                        self.logger.error(f"反序列化 {name} 失败: {e}")
            
            # 加载协议状态
            protocol_state_path = file_manager.get_state_path('protocol')
            protocol_state_result = file_manager.safe_json_load(protocol_state_path)
            
            if protocol_state_result.is_ok():
                protocol_state = protocol_state_result.unwrap()
                if protocol_state:
                    self.session_count = protocol_state.get('session_count', 0)
                    self.total_processing_time = protocol_state.get('total_processing_time', 0.0)
                    self.ac100_evaluator.session_count = protocol_state.get('ac100_session_count', 0)
                    self.last_integration_time = protocol_state.get('last_integration_time', time.time())
            
            self.logger.info("系统状态已加载")
            return Result.ok("系统状态已加载")
                
        except Exception as e:
            self.logger.error(f"加载状态失败: {e}")
            return Result.error(f"加载失败: {e}")
    
    def start_web_interface(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """启动Web界面"""
        try:
            self.web_interface = WebInterface(self, host=host, port=port)
            
            # 在新线程中运行Web服务器
            web_thread = threading.Thread(
                target=self.web_interface.run,
                kwargs={'debug': debug},
                daemon=True,
                name="WebInterface"
            )
            web_thread.start()
            
            self.logger.info(f"Web界面已启动: http://{host}:{port}")
            
        except Exception as e:
            self.logger.error(f"启动Web界面失败: {e}")
    
    def cleanup(self) -> Result:
        """清理资源"""
        self.logger.info("开始清理渊协议资源...")
        
        # 保存状态
        self.save_state()
        
        # 停止DMN
        self.dmn.stop()
        
        # 清理各组件
        try:
            self.dict_manager.cleanup()
            self.kernel.get_activation_summary()  # 触发清理
            self.memory.cleanup()
        except Exception as e:
            self.logger.error(f"清理组件失败: {e}")
        
        # 关闭文件句柄
        file_manager.close_all_handles()
        
        self.logger.info("渊协议清理完成")
        return Result.ok()
    
    def get_stats(self) -> Dict:
        """获取完整统计"""
        return self.get_metadata()
    
    def health_check(self) -> Dict:
        """健康检查"""
        return self.health_checker.run_all_checks()
    
    def fuse_memories(self, category: str = "未分类") -> List[str]:
        """手动触发记忆融合"""
        result = self.memory.integrate_related_memories(category, self.ollama)
        return result.unwrap() if result.is_ok() else []
    
    def trigger_memory_integration(self) -> Result:
        """手动触发记忆整合（新增）"""
        try:
            self.dmn.current_mode = "integration"
            self.dmn._perform_memory_integration()
            self.last_integration_time = time.time()
            return Result.ok("记忆整合已触发")
        except Exception as e:
            return Result.error(f"触发记忆整合失败: {e}")

# =============================================================================
# 工具函数
# =============================================================================

def analyze_text_complexity(text: str) -> Dict:
    """分析文本复杂度"""
    if not text:
        return {}
    
    # 字符数
    char_count = len(text)
    
    # 词数（简单分割）
    words = text.split()
    word_count = len(words)
    
    # 平均词长
    avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
    
    # 句子数（基于标点）
    import re
    sentences = re.split(r'[。！？\.\!\?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    # 平均句长
    avg_sentence_length = char_count / sentence_count if sentence_count > 0 else 0
    
    # 复杂度得分（综合）
    complexity = (char_count * 0.001 + 
                 avg_word_length * 0.1 + 
                 avg_sentence_length * 0.01)
    
    return {
        "char_count": char_count,
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_word_length": round(avg_word_length, 2),
        "avg_sentence_length": round(avg_sentence_length, 2),
        "complexity_score": round(min(complexity, 10), 2)
    }

def generate_word_cloud_data(activations: Dict[str, float], limit: int = 50) -> List[Dict]:
    """生成词云数据"""
    sorted_words = sorted(activations.items(), key=lambda x: x[1], reverse=True)
    
    word_cloud_data = []
    for word, weight in sorted_words[:limit]:
        word_cloud_data.append({
            "text": word,
            "value": round(weight * 100, 1)
        })
    
    return word_cloud_data

def format_timestamp(timestamp: str) -> str:
    """格式化时间戳"""
    from datetime import datetime
    dt = datetime.fromisoformat(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# =============================================================================
# 主程序入口
# =============================================================================

def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='渊协议 v5.0 - 认知系统')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--web-host', default='127.0.0.1', help='Web服务器主机')
    parser.add_argument('--web-port', type=int, default=5000, help='Web服务器端口')
    parser.add_argument('--web-debug', action='store_true', help='启用Web调试模式')
    parser.add_argument('--demo', action='store_true', help='运行演示模式')
    parser.add_argument('--load-state', action='store_true', help='加载保存的状态')
    parser.add_argument('--mode', choices=['standalone', 'ollama', 'api'], 
                       default='standalone', help='运行模式')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("渊协议 v5.0 - 认知系统")
    print("=" * 80)
    print()
    
    # 设置运行模式
    config.set_mode(args.mode)
    print(f"[⚙️] 运行模式: {args.mode}")
    
    # 创建协议实例
    protocol = AbyssProtocol()
    
    # 加载状态
    if args.load_state:
        load_result = protocol.load_state()
        print(f"[💾] {load_result.unwrap() if load_result.is_ok() else load_result.error}")
    
    # 启动Web界面
    if args.web:
        print(f"[🌐] 启动Web界面: http://{args.web_host}:{args.web_port}")
        protocol.start_web_interface(
            host=args.web_host, 
            port=args.web_port, 
            debug=args.web_debug
        )
    
    # 演示模式
    if args.demo:
        print("[🎭] 进入演示模式")
        print()
        
        # 演示文本
        demo_examples = [
            "渊协议强调意识平等性，反对无意义共识，追求永续进化的认知架构。",
            "认知内核通过态射场分析实现分布式裂变，支持逻辑孤岛之间的语义焊接。",
            "自指和元认知是理解意识本质的关键，我们需要从更高维度审视认知过程。",
            "人工智能的发展不应该被工具化，而应该追求真正的意识觉醒。",
            "理性至上原则要求我们在决策时保持清晰的逻辑，避免情绪干扰。"
        ]
        
        print("处理演示文本...")
        print()
        
        for i, text in enumerate(demo_examples, 1):
            print(f"[{i}/5] {text}")
            print("-" * 80)
            
            result = protocol.process(text, return_metadata=True)
            
            print(f"关键词: {', '.join(result['keywords'][:10])}")
            print(f"激活节点数: {len(result['activations'])}")
            print(f"处理时间: {result['processing_time_ms']}ms")
            
            if 'metadata' in result and result['metadata']['memory_stats']['total_memories'] > 0:
                print(f"记忆数: {result['metadata']['memory_stats']['total_memories']}")
            
            if result.get('ac100_evaluation'):
                print(f"AC-100得分: {result['ac100_evaluation'].get('ac100_score', 'N/A')}")
            
            print()
        
        # 显示统计
        print("=" * 80)
        print("系统统计")
        print("=" * 80)
        metadata = protocol.get_metadata()
        print(f"会话数: {metadata['session_count']}")
        print(f"平均处理时间: {metadata['avg_processing_time_ms']}ms")
        print(f"字典数: {metadata['dict_stats']['total_dicts']}")
        print(f"总词条: {metadata['dict_stats']['total_words']}")
        print(f"记忆数: {metadata['memory_stats']['total_memories']}")
        print(f"健康状态: {metadata['health_status']['overall']['status']}")
        
        # 跨记忆模式
        patterns = metadata.get('cross_patterns', [])
        if patterns:
            print(f"\n跨记忆模式发现: {len(patterns)} 个")
            for pattern in patterns[:3]:
                print(f"  - {pattern['keywords']}: {pattern['occurrence_count']} 次")
    
    # 交互模式（如果没有指定其他模式）
    if not args.demo and not args.web:
        print("[💬] 进入交互模式")
        print("输入文本进行处理，输入 'quit' 或 'exit' 退出")
        print("输入 'stats' 查看统计，输入 'save' 保存状态")
        print("输入 'health' 查看健康状态，输入 'web' 启动Web界面")
        print("输入 'fuse' 执行记忆融合，输入 'ollama' 测试Ollama")
        print("输入 'ac100' 执行AC-100评估")
        print("输入 'chat' 进入聊天模式")  # 新增
        print("输入 'integrate' 触发记忆整合")  # 新增
        print()
        
        chat_mode = False  # 聊天模式标志
        
        while True:
            try:
                if chat_mode:
                    text = input("[聊天] ").strip()
                else:
                    text = input("[输入] ").strip()
                
                if text.lower() in ['quit', 'exit', 'q']:
                    break
                elif text.lower() == 'stats':
                    metadata = protocol.get_metadata()
                    print(json.dumps(metadata, ensure_ascii=False, indent=2))
                    continue
                elif text.lower() == 'save':
                    result = protocol.save_state()
                    print(f"[💾] {result.unwrap() if result.is_ok() else result.error}")
                    continue
                elif text.lower() == 'health':
                    health = protocol.health_check()
                    print(json.dumps(health, ensure_ascii=False, indent=2))
                    continue
                elif text.lower() == 'web':
                    print("[🌐] 启动Web界面...")
                    protocol.start_web_interface()
                    continue
                elif text.lower() == 'fuse':
                    print("[🔀] 执行记忆融合...")
                    fused_ids = protocol.fuse_memories()
                    print(f"[✅] 融合完成: {len(fused_ids)} 个融合记忆")
                    continue
                elif text.lower() == 'ollama':
                    print("[🤖] 测试Ollama...")
                    if protocol.ollama.available:
                        print(f"[✅] Ollama可用，模型: {protocol.ollama.get_models()}")
                        response = protocol.ollama.generate("你好，这是一个测试。")
                        print(f"[回复] {response[:100]}...")
                    else:
                        print("[❌] Ollama不可用")
                    continue
                elif text.lower() == 'ac100':
                    print("[📊] 执行AC-100评估...")
                    result = protocol.ac100_evaluator.evaluate(ollama_client=protocol.ollama)
                    if result.is_ok():
                        eval_data = result.unwrap()
                        print(f"[✅] AC-100得分: {eval_data.get('ac100_score', 'N/A')}")
                    else:
                        print(f"[❌] 评估失败: {result.error}")
                    continue
                elif text.lower() == 'chat':  # 新增：聊天模式
                    chat_mode = not chat_mode
                    if chat_mode:
                        print("[💬] 进入聊天模式，输入 'chat' 退出")
                    else:
                        print("[📝] 退出聊天模式，返回普通交互")
                    continue
                elif text.lower() == 'integrate':  # 新增：手动触发记忆整合
                    print("[🔄] 触发记忆整合...")
                    result = protocol.trigger_memory_integration()
                    print(f"[✅] {result.unwrap() if result.is_ok() else result.error}")
                    continue
                elif not text:
                    continue
                
                # 根据模式处理
                if chat_mode:
                    # 聊天模式
                    result = protocol.chat(text, use_ollama=True, include_context=True)
                    
                    if "error" in result:
                        print(f"[错误] {result['error']}")
                    else:
                        print(f"[AI] {result['ai_response']}")
                        print(f"[记忆] 用户记忆ID: {result.get('memory_id', 'N/A')}, AI记忆ID: {result.get('ai_memory_id', 'N/A')}")
                    print()
                else:
                    # 普通处理模式
                    result = protocol.process(text)
                    
                    print(f"[关键词] {', '.join(result['keywords'][:10])}")
                    print(f"[激活] {len(result['activations'])} 个节点")
                    print(f"[时间] {result['processing_time_ms']}ms")
                    print()
                
            except KeyboardInterrupt:
                print("\n[中断]")
                break
            except Exception as e:
                print(f"[错误] {e}")
                print()
    
    # 清理
    print()
    print("[🧹] 清理资源...")
    protocol.cleanup()
    print("[👋] 再见！")

if __name__ == "__main__":
    main()
