#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议内核 - MCP架构核心

集成所有组件，提供统一的API接口。
"""

import time
import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config_manager import config
from .logger import AbyssLogger, log_performance
from .memory_monitor import memory_monitor
from ..core.cache_system import cache_manager
from .event_system import event_system, SystemEvents

from ..models.dictionary_manager import DictionaryManager
from ..models.memory_system import MemorySystem, MemoryLayer
from ..models.cognitive_kernel import CognitiveKernel
from ..models.tokenizer import LightweightTokenizer

from ..controllers.api_controller import APIController
from ..controllers.memory_controller import MemoryController
from ..controllers.dictionary_controller import DictionaryController

from ..plugins.plugin_manager import plugin_manager


class AbyssKernel:
    """
    渊协议内核 - MCP架构核心
    
    集成以下组件：
    - DictionaryManager: 分布式字典管理
    - MemorySystem: 四层记忆系统
    - CognitiveKernel: 认知激活核心
    - LightweightTokenizer: 分词器
    - APIController: API控制器
    - PluginManager: 插件管理器
    """
    
    def __init__(self):
        self.logger = AbyssLogger("AbyssKernel")
        
        # 启动时间
        self.start_time = time.time()
        
        # 初始化组件
        self.logger.info("初始化渊协议内核...")
        
        # 1. 字典管理器
        self.dict_manager = DictionaryManager()
        self.logger.info("✅ 字典管理器初始化完成")
        
        # 2. 分词器
        self.tokenizer = LightweightTokenizer(dict_manager=self.dict_manager)
        self.logger.info("✅ 分词器初始化完成")
        
        # 3. 记忆系统
        self.memory = MemorySystem(dict_manager=self.dict_manager, kernel=self)
        self.logger.info("✅ 记忆系统初始化完成")
        
        # 4. 认知内核
        self.cognitive = CognitiveKernel(dict_manager=self.dict_manager, tokenizer=self.tokenizer)
        self.logger.info("✅ 认知内核初始化完成")
        
        # 5. 控制器
        self.memory_controller = MemoryController(self.memory)
        self.dictionary_controller = DictionaryController(self.dict_manager)
        self.api_controller = APIController(self)
        self.logger.info("✅ 控制器初始化完成")
        
        # 6. 插件管理器（延迟初始化）
        self.plugin_manager = plugin_manager
        self.logger.info("✅ 插件管理器就绪")
        
        # 状态
        self.initialized = False
        self.running = False
        
        # 自动保存线程
        self.auto_save_thread = None
        self._stop_auto_save = threading.Event()
        
        # 健康检查线程
        self.health_check_thread = None
        self._stop_health_check = threading.Event()
        
        self.logger.info("渊协议内核初始化完成")
    
    def initialize(self):
        """初始化系统"""
        if self.initialized:
            return
        
        self.logger.info("开始系统初始化...")
        
        # 1. 启动内存监控
        memory_monitor.start_monitoring()
        self.logger.info("✅ 内存监控已启动")
        
        # 2. 初始化插件
        self.plugin_manager.initialize_plugins(self)
        self.logger.info("✅ 插件初始化完成")
        
        # 3. 自动加载插件
        self.plugin_manager.auto_load_plugins()
        self.logger.info("✅ 插件自动加载完成")
        
        # 4. 启动API服务器
        if config.get('api.enabled', True):
            self.api_controller.start_server()
            self.logger.info("✅ API服务器已启动")
        
        # 5. 启动后台线程
        self._start_background_threads()
        self.logger.info("✅ 后台线程已启动")
        
        self.initialized = True
        self.running = True
        
        # 触发系统启动事件
        event_system.emit(SystemEvents.SYSTEM_STARTUP, {
            'timestamp': datetime.now().isoformat(),
            'version': '4.0.0',
            'components': self.get_stats()
        })
        
        self.logger.info("✅ 系统初始化完成，准备就绪！")
    
    def _start_background_threads(self):
        """启动后台线程"""
        # 自动保存线程
        interval = config.get('system.auto_save_interval', 300)
        self.auto_save_thread = threading.Thread(
            target=self._auto_save_loop,
            args=(interval,),
            daemon=True
        )
        self.auto_save_thread.start()
        
        # 健康检查线程
        check_interval = config.get('system.health_check_interval', 60)
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            args=(check_interval,),
            daemon=True
        )
        self.health_check_thread.start()
    
    def _auto_save_loop(self, interval: int):
        """自动保存循环"""
        while not self._stop_auto_save.is_set():
            try:
                self.save_state()
                self.logger.debug(f"自动保存完成")
            except Exception as e:
                self.logger.error(f"自动保存失败: {e}")
            
            self._stop_auto_save.wait(interval)
    
    def _health_check_loop(self, interval: int):
        """健康检查循环"""
        while not self._stop_health_check.is_set():
            try:
                # 检查内存使用
                memory_info = memory_monitor.get_current_memory_usage()
                memory_mb = memory_info.get('memory_mb', 0)
                max_memory = config.get('system.max_memory_mb', 500)
                
                if memory_mb > max_memory:
                    self.logger.warning(f"内存使用过高: {memory_mb:.1f}MB / {max_memory}MB")
                    
                    # 尝试清理
                    memory_monitor.force_gc()
                
                # 检查系统状态
                stats = self.get_stats()
                self.logger.debug(f"健康检查完成: {stats}")
                
            except Exception as e:
                self.logger.error(f"健康检查失败: {e}")
            
            self._stop_health_check.wait(interval)
    
    @log_performance
    def process(self, text: str, return_metadata: bool = False) -> Dict[str, Any]:
        """处理文本 - 核心功能"""
        if not self.initialized:
            raise RuntimeError("内核未初始化，请先调用initialize()")
        
        start_time = time.time()
        
        try:
            # 1. 分词
            keywords = self.tokenizer.tokenize(text, return_weights=True)
            keyword_list = [kw[0] for kw in keywords]
            
            # 2. 认知激活
            activations = self.cognitive.activate(text)
            
            # 3. 创建记忆
            memory_id = self.memory.create_memory(
                content=text,
                layer=MemoryLayer.CATEGORICAL,
                category="未分类",
                metadata={
                    'activations': activations,
                    'keyword_count': len(keywords),
                    'keywords': keyword_list
                }
            )
            
            # 4. 添加到字典
            for keyword, weight in keywords:
                if weight > 0.5:  # 只添加重要关键词
                    self.dict_manager.add_word(keyword)
            
            # 构建结果
            result = {
                'success': True,
                'memory_id': memory_id,
                'keywords': keyword_list,
                'keyword_count': len(keywords),
                'activations': activations,
                'activation_count': len(activations),
                'processing_time': time.time() - start_time
            }
            
            if return_metadata:
                result.update({
                    'cognitive_patterns': self.cognitive.get_cognitive_patterns(),
                    'drift_analysis': self.cognitive.get_drift_analysis(),
                    'memory_stats': self.memory.get_stats(),
                    'dictionary_stats': self.dict_manager.get_stats()
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save_state(self, path: str = None):
        """保存系统状态"""
        try:
            save_path = Path(path or config.get('system.base_path', './abyss_mcp_data')) / 'kernel_state.json'
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            state = {
                'version': '4.0.0',
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time() - self.start_time,
                'kernel': self.serialize_state(),
                'dictionary': self.dict_manager.serialize_state(),
                'memory': self.memory.serialize_state(),
                'cognitive': self.cognitive.serialize_state(),
                'plugins': self.plugin_manager.get_plugin_stats()
            }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"状态已保存: {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存状态失败: {e}")
            return False
    
    def load_state(self, path: str = None):
        """加载系统状态"""
        try:
            load_path = Path(path or config.get('system.base_path', './abyss_mcp_data')) / 'kernel_state.json'
            
            if not load_path.exists():
                self.logger.warning(f"状态文件不存在: {load_path}")
                return False
            
            with open(load_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 反序列化各组件状态
            if 'dictionary' in state:
                self.dict_manager.deserialize_state(state['dictionary'])
            
            if 'memory' in state:
                self.memory.deserialize_state(state['memory'])
            
            if 'cognitive' in state:
                self.cognitive.deserialize_state(state['cognitive'])
            
            self.logger.info(f"状态已加载: {load_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载状态失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计"""
        return {
            'uptime': time.time() - self.start_time,
            'initialized': self.initialized,
            'running': self.running,
            'memory_usage': memory_monitor.get_current_memory_usage(),
            'dictionary': self.dict_manager.get_stats(),
            'memory': self.memory.get_stats(),
            'cognitive': self.cognitive.get_activation_summary(),
            'plugins': self.plugin_manager.get_plugin_stats(),
            'api': {
                'request_count': self.api_controller.request_count if hasattr(self.api_controller, 'request_count') else 0
            }
        }
    
    def cleanup(self):
        """清理系统资源"""
        self.logger.info("开始清理系统资源...")
        
        # 停止后台线程
        self._stop_auto_save.set()
        self._stop_health_check.set()
        
        if self.auto_save_thread:
            self.auto_save_thread.join(timeout=5)
        
        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)
        
        # 停止API服务器
        self.api_controller.stop_server()
        
        # 清理插件
        self.plugin_manager.cleanup()
        
        # 清理各组件
        self.memory.cleanup()
        self.dict_manager.cleanup()
        self.tokenizer.cleanup()
        self.cognitive.cleanup()
        
        # 清理缓存
        cache_manager.clear_all()
        
        # 停止内存监控
        memory_monitor.stop_monitoring()
        
        # 保存最终状态
        self.save_state()
        
        self.running = False
        self.logger.info("系统清理完成")
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化内核状态"""
        return {
            'version': '4.0.0',
            'start_time': self.start_time,
            'uptime': time.time() - self.start_time,
            'initialized': self.initialized,
            'running': self.running
        }
    
    def deserialize_state(self, state: Dict[str, Any]):
        """反序列化内核状态"""
        # 内核状态主要用于记录，实际恢复逻辑在load_state中处理
        pass


# 全局内核实例
kernel = AbyssKernel()