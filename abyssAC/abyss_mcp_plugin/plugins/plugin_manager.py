#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件管理器 - 插件系统核心

管理插件的加载、卸载、配置和生命周期。
"""

import os
import sys
import json
import time
import importlib
import importlib.util
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
from collections import defaultdict
from ..core.logger import AbyssLogger
from ..core.event_system import event_system, SystemEvents

from .plugin_base import PluginBase, PluginInfo, PluginType
from ..core.config_manager import config
from ..core.logger import AbyssLogger
from ..core.event_system import event_system, SystemEvents


class PluginManager:
    """
    插件管理器
    
    功能：
    - 自动发现和加载插件
    - 插件生命周期管理
    - 插件配置管理
    - 插件间通信
    - 安全沙箱（基础版）
    """
    
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_classes: Dict[str, Type[PluginBase]] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # 插件目录
        self.plugin_dirs = config.get('plugins.plugin_dirs', ['./plugins', './custom_plugins'])
        
        # 安全模式
        self.safe_mode = config.get('plugins.safe_mode', True)
        self.blacklist = set(config.get('plugins.blacklist', []))
        self.whitelist = set(config.get('plugins.whitelist', []))
        
        # 状态
        self.initialized = False
        self._lock = threading.RLock()
        
        # 配置路径
        self.config_path = Path(config.get('system.base_path', './abyss_mcp_data')) / 'plugin_configs.json'
        
        self.logger = AbyssLogger("PluginManager")
        
        # 加载插件配置
        self._load_plugin_configs()
        
        self.logger.info("插件管理器初始化完成")
    
    def _load_plugin_configs(self):
        """加载插件配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.plugin_configs = json.load(f)
        except Exception as e:
            self.logger.warning(f"加载插件配置失败: {e}")
            self.plugin_configs = {}
    
    def _save_plugin_configs(self):
        """保存插件配置"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.plugin_configs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存插件配置失败: {e}")
    
    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                continue
            
            # 查找插件文件
            for plugin_file in plugin_path.glob("*.py"):
                if plugin_file.name.startswith("__"):
                    continue
                
                plugin_name = plugin_file.stem
                
                # 安全检查
                if self.safe_mode:
                    if self.blacklist and plugin_name in self.blacklist:
                        self.logger.warning(f"跳过黑名单插件: {plugin_name}")
                        continue
                    
                    if self.whitelist and plugin_name not in self.whitelist:
                        self.logger.warning(f"跳过非白名单插件: {plugin_name}")
                        continue
                
                discovered.append(str(plugin_file))
        
        return discovered
    
    def load_plugin(self, plugin_path: str) -> bool:
        """加载单个插件"""
        try:
            plugin_file = Path(plugin_path)
            plugin_name = plugin_file.stem
            
            # 检查是否已加载
            if plugin_name in self.plugins:
                self.logger.warning(f"插件已加载: {plugin_name}")
                return True
            
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_file)
            if spec is None or spec.loader is None:
                self.logger.error(f"无法加载插件模块: {plugin_name}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginBase) and 
                    attr != PluginBase):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                self.logger.error(f"插件中未找到插件类: {plugin_name}")
                return False
            
            # 获取插件信息
            if hasattr(plugin_class, 'PLUGIN_INFO'):
                plugin_info = PluginInfo(**plugin_class.PLUGIN_INFO)
            else:
                # 默认信息
                plugin_info = PluginInfo(
                    name=plugin_name,
                    version="1.0.0",
                    description=f"Plugin {plugin_name}",
                    author="Unknown",
                    type=PluginType.INTEGRATION,
                    dependencies=[]
                )
            
            # 检查依赖
            if not self._check_dependencies(plugin_info.dependencies):
                self.logger.error(f"插件依赖不满足: {plugin_name}")
                return False
            
            # 创建插件实例
            plugin_instance = plugin_class(plugin_info)
            
            # 加载配置
            if plugin_name in self.plugin_configs:
                plugin_instance.update_config(self.plugin_configs[plugin_name])
            
            # 注册插件
            with self._lock:
                self.plugins[plugin_name] = plugin_instance
                self.plugin_classes[plugin_name] = plugin_class
            
            self.logger.info(f"插件加载成功: {plugin_name}")
            
            # 触发事件
            event_system.emit(SystemEvents.PLUGIN_LOADED, {
                'plugin_name': plugin_name,
                'plugin_type': plugin_info.type.value
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载插件失败: {plugin_path} - {str(e)}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        with self._lock:
            if plugin_name not in self.plugins:
                self.logger.warning(f"插件未加载: {plugin_name}")
                return False
            
            try:
                # 清理插件
                plugin = self.plugins[plugin_name]
                plugin.cleanup()
                
                # 移除插件
                del self.plugins[plugin_name]
                del self.plugin_classes[plugin_name]
                
                self.logger.info(f"插件卸载成功: {plugin_name}")
                
                # 触发事件
                event_system.emit(SystemEvents.PLUGIN_UNLOADED, {
                    'plugin_name': plugin_name
                })
                
                return True
                
            except Exception as e:
                self.logger.error(f"卸载插件失败: {plugin_name} - {str(e)}")
                return False
    
    def initialize_plugins(self, kernel):
        """初始化所有插件"""
        if self.initialized:
            return
        
        with self._lock:
            for plugin_name, plugin in self.plugins.items():
                try:
                    plugin_config = self.plugin_configs.get(plugin_name, {})
                    plugin.initialize(kernel, plugin_config)
                    self.logger.info(f"插件初始化成功: {plugin_name}")
                except Exception as e:
                    self.logger.error(f"初始化插件失败: {plugin_name} - {str(e)}")
                    # 禁用失败的插件
                    plugin.disable()
            
            self.initialized = True
    
    def _check_dependencies(self, dependencies: List[str]) -> bool:
        """检查依赖是否满足"""
        for dep in dependencies:
            if dep not in self.plugins:
                return False
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取插件实例"""
        with self._lock:
            return self.plugins.get(plugin_name)
    
    def get_loaded_plugins(self) -> Dict[str, PluginInfo]:
        """获取已加载的插件信息"""
        with self._lock:
            return {
                name: plugin.get_info()
                for name, plugin in self.plugins.items()
            }
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginBase]:
        """按类型获取插件"""
        with self._lock:
            return [
                plugin for plugin in self.plugins.values()
                if plugin.info.type == plugin_type and plugin.is_enabled()
            ]
    
    def update_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """更新插件配置"""
        with self._lock:
            if plugin_name not in self.plugins:
                return False
            
            try:
                plugin = self.plugins[plugin_name]
                plugin.update_config(config)
                
                # 保存配置
                self.plugin_configs[plugin_name] = plugin.get_config()
                self._save_plugin_configs()
                
                self.logger.info(f"插件配置更新: {plugin_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"更新插件配置失败: {plugin_name} - {str(e)}")
                return False
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件"""
        with self._lock:
            if plugin_name not in self.plugins:
                return False
            
            self.plugins[plugin_name].enable()
            self.logger.info(f"插件启用: {plugin_name}")
            return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件"""
        with self._lock:
            if plugin_name not in self.plugins:
                return False
            
            self.plugins[plugin_name].disable()
            self.logger.info(f"插件禁用: {plugin_name}")
            return True
    
    def auto_load_plugins(self):
        """自动加载插件"""
        if not config.get('plugins.auto_load', True):
            return
        
        discovered = self.discover_plugins()
        loaded_count = 0
        
        for plugin_path in discovered:
            if self.load_plugin(plugin_path):
                loaded_count += 1
        
        self.logger.info(f"自动加载插件完成: {loaded_count}/{len(discovered)}")
    
    def call_plugin_method(self, plugin_name: str, method_name: str, *args, **kwargs):
        """调用插件方法"""
        with self._lock:
            if plugin_name not in self.plugins:
                raise ValueError(f"插件未加载: {plugin_name}")
            
            plugin = self.plugins[plugin_name]
            if not plugin.is_enabled():
                raise RuntimeError(f"插件已禁用: {plugin_name}")
            
            if not hasattr(plugin, method_name):
                raise AttributeError(f"插件没有方法: {method_name}")
            
            method = getattr(plugin, method_name)
            return method(*args, **kwargs)
    
    def broadcast_to_plugins(self, event_name: str, data: Dict[str, Any]):
        """广播事件到所有插件"""
        with self._lock:
            for plugin_name, plugin in self.plugins.items():
                if plugin.is_enabled() and hasattr(plugin, 'on_event'):
                    try:
                        plugin.on_event(event_name, data)
                    except Exception as e:
                        self.logger.error(f"插件事件处理失败: {plugin_name} - {str(e)}")
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """获取插件统计"""
        with self._lock:
            type_counts = defaultdict(int)
            status_counts = {'enabled': 0, 'disabled': 0}
            
            for plugin in self.plugins.values():
                type_counts[plugin.info.type.value] += 1
                if plugin.is_enabled():
                    status_counts['enabled'] += 1
                else:
                    status_counts['disabled'] += 1
            
            return {
                'total_plugins': len(self.plugins),
                'type_distribution': dict(type_counts),
                'status_distribution': status_counts,
                'plugin_names': list(self.plugins.keys())
            }
    
    def cleanup(self):
        """清理所有插件"""
        self.logger.info("开始清理插件...")
        
        with self._lock:
            for plugin_name, plugin in self.plugins.items():
                try:
                    plugin.cleanup()
                    self.logger.info(f"插件清理完成: {plugin_name}")
                except Exception as e:
                    self.logger.error(f"清理插件失败: {plugin_name} - {str(e)}")
            
            self.plugins.clear()
            self.plugin_classes.clear()
        
        self.logger.info("插件清理完成")


# 全局插件管理器实例
plugin_manager = PluginManager()