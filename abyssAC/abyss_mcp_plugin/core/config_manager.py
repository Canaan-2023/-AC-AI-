#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - MCP架构配置系统
"""

import os
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Union


class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


class ConfigManager:
    """
    配置管理器 - 单例模式，线程安全
    
    支持配置的热加载和动态更新，提供完整的线程安全保护。
    """
    _instance = None
    _lock = threading.RLock()
    _initialized = False
    
    def __new__(cls, config_path: str = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self, config_path: str = None):
        # 确保只初始化一次
        with self._lock:
            if self._initialized:
                return
            self._initialized = True
            
            self._config = {}
            self._config_lock = threading.RLock()
            self._config_path = config_path or "config/abyss_config.json"
            self._load_default_config()
            self._load_from_file()
    
    def _load_default_config(self):
        """加载默认配置"""
        with self._config_lock:
            self._config = {
                # 系统配置
                "system": {
                    "name": "AbyssMCP",
                    "version": "4.0.0",
                    "auto_save_interval": 300,
                    "health_check_interval": 60,
                    "enable_metrics": True,
                    "max_memory_mb": 500,
                    "base_path": "./abyss_mcp_data",
                    "plugin_path": "./plugins"
                },
                # 字典配置
                "dictionary": {
                    "max_dict_size": 5000,
                    "max_dict_files": 20,
                    "activation_threshold": 0.3,
                    "fission_enabled": True,
                    "fission_check_interval": 100,
                    "split_threshold": 0.8,
                    "merge_threshold": 0.3,
                    "cache_size": 1000,
                    "shadow_index_size": 1000,
                    "index_max_size": 10000,
                    "index_lru_size": 1000,
                    "segment_lock_count": 8
                },
                # 分词器配置
                "tokenizer": {
                    "cache_size": 1000,
                    "enable_activation_cache": True,
                    "activation_cache_size": 500,
                    "max_keywords_per_text": 15,
                    "min_word_length": 2,
                    "max_word_length": 20,
                    "extract_english": True,
                    "extract_numbers": False,
                    "remove_punctuation": True,
                    "dict_word_boost": 1.5
                },
                # 认知配置
                "cognitive": {
                    "enable_propagation": True,
                    "score_base_value": 0.1,
                    "complexity_weight": 0.3,
                    "confidence_weight": 0.7,
                    "depth_weight": 0.3,
                    "match_score_weight": 0.6,
                    "high_score_threshold": 0.7,
                    "medium_score_threshold": 0.5,
                    "low_score_threshold": 0.3,
                    "complexity_max_chars": 2000,
                    "complexity_max_sentences": 20,
                    "drift_log_keep": 50,
                    "activation_cache_size": 500,
                    "enable_activation_cache": True
                },
                # X层配置
                "xlayer": {
                    "symbol_ttl_hours": 24,
                    "max_symbols": 30,
                    "backup_history_size": 10
                },
                # AC-100配置
                "ac100": {
                    "evaluation_interval": 5,
                    "dimension_weights": {
                        "self_reference": 0.15,
                        "value_autonomy": 0.15,
                        "cognitive_growth": 0.15,
                        "memory_continuity": 0.15,
                        "prediction_imagination": 0.15,
                        "environment_interaction": 0.1,
                        "explanation_transparency": 0.15
                    }
                },
                # 记忆配置
                "memory": {
                    "working_memory_size": 100,
                    "max_memory_per_layer": 1000,
                    "cleanup_interval": 3600,
                    "importance_threshold": 0.5,
                    "fuse_similarity_threshold": 0.7,
                    "cleanup_batch_size": 10,
                    "time_decay_hours": 168
                },
                # 拓扑配置
                "topology": {
                    "max_path_length": 8,
                    "max_expansions": 50,
                    "max_candidate_paths": 20,
                    "novelty_weight": 0.3,
                    "coherence_weight": 0.5,
                    "relevance_weight": 0.2,
                    "cache_ttl_seconds": 300
                },
                # API配置
                "api": {
                    "enabled": True,
                    "host": "127.0.0.1",
                    "port": 8080,
                    "debug": False,
                    "cors_enabled": True,
                    "rate_limit": {
                        "enabled": True,
                        "requests_per_minute": 60
                    }
                },
                # 插件配置
                "plugins": {
                    "enabled": True,
                    "auto_load": True,
                    "plugin_dirs": ["./plugins", "./custom_plugins"],
                    "safe_mode": True,
                    "blacklist": [],
                    "whitelist": []
                },
                # 性能配置
                "performance": {
                    "cache_ttl_seconds": 300,
                    "enable_async_tasks": True,
                    "max_thread_workers": 10,
                    "io_timeout": 30,
                    "gc_threshold": 10000
                }
            }
    
    def _load_from_file(self):
        """从配置文件加载"""
        try:
            config_file = Path(self._config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self.update(file_config)
                print(f"[✅] 配置文件加载成功: {self._config_path}")
        except Exception as e:
            print(f"[⚠️] 配置文件加载失败: {e}，使用默认配置")
    
    def save_to_file(self, path: str = None):
        """保存配置到文件"""
        try:
            save_path = path or self._config_path
            config_dir = Path(save_path).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[❌] 配置保存失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        with self._config_lock:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        with self._config_lock:
            keys = key.split(".")
            config = self._config
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
    
    def update(self, config_dict: Dict):
        """更新配置"""
        with self._config_lock:
            self._deep_merge(self._config, config_dict)
    
    def _deep_merge(self, base: Dict, override: Dict):
        """深度合并字典"""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def export(self) -> Dict:
        """导出完整配置"""
        with self._config_lock:
            return dict(self._config)
    
    def validate(self) -> bool:
        """验证配置有效性"""
        required_keys = [
            "system.base_path",
            "dictionary.max_dict_size", 
            "api.port",
            "memory.max_memory_per_layer"
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                raise ConfigValidationError(f"缺少必需配置项: {key}")
        
        return True


# 全局配置实例
config = ConfigManager()