"""AbyssAC系统配置管理模块

管理系统所有配置项，提供配置加载、验证和访问功能。
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path


@dataclass
class LLMConfig:
    """LLM配置"""
    api_type: str = "ollama"
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5:latest"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    retry_count: int = 3


@dataclass
class SystemConfig:
    """系统核心配置"""
    max_navigation_depth: int = 10
    navigation_timeout: int = 30
    dmn_auto_trigger: bool = True
    dmn_idle_threshold: int = 300  # 5分钟
    dmn_memory_threshold: int = 20
    dmn_failure_threshold: int = 5
    max_working_memory: int = 50


@dataclass
class PathConfig:
    """路径配置"""
    base: str = "/mnt/okcomputer/output/AbyssAC"
    y_layer: str = "storage/Y层记忆库"
    nng: str = "storage/nng"
    system: str = "storage/system"
    logs: str = "storage/system/logs"


@dataclass
class ConfidenceConfig:
    """置信度配置"""
    display_threshold: int = 30
    delete_threshold: int = 10
    default_new: int = 70


class Config:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.json"
        self.llm = LLMConfig()
        self.system = SystemConfig()
        self.paths = PathConfig()
        self.confidence = ConfidenceConfig()
        self._loaded = False
    
    def load(self) -> bool:
        """从文件加载配置"""
        if not os.path.exists(self.config_path):
            return False
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'llm' in data:
                self.llm = LLMConfig(**data['llm'])
            if 'system' in data:
                self.system = SystemConfig(**data['system'])
            if 'paths' in data:
                self.paths = PathConfig(**data['paths'])
            if 'confidence' in data:
                self.confidence = ConfidenceConfig(**data['confidence'])
            
            self._loaded = True
            return True
        except Exception as e:
            print(f"配置加载失败: {e}")
            return False
    
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            data = {
                'llm': asdict(self.llm),
                'system': asdict(self.system),
                'paths': asdict(self.paths),
                'confidence': asdict(self.confidence)
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"配置保存失败: {e}")
            return False
    
    def get_full_path(self, relative_path: str) -> str:
        """获取完整路径"""
        base = Path(self.paths.base)
        return str(base / relative_path)
    
    def ensure_directories(self) -> None:
        """确保所有目录存在"""
        dirs = [
            self.get_full_path(self.paths.y_layer),
            self.get_full_path(f"{self.paths.y_layer}/元认知记忆"),
            self.get_full_path(f"{self.paths.y_layer}/高阶整合记忆"),
            self.get_full_path(f"{self.paths.y_layer}/分类记忆/高价值"),
            self.get_full_path(f"{self.paths.y_layer}/分类记忆/中价值"),
            self.get_full_path(f"{self.paths.y_layer}/分类记忆/低价值"),
            self.get_full_path(f"{self.paths.y_layer}/工作记忆"),
            self.get_full_path(self.paths.nng),
            self.get_full_path(self.paths.system),
            self.get_full_path(self.paths.logs),
        ]
        
        for d in dirs:
            os.makedirs(d, exist_ok=True)


# 全局配置实例
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config(config_path)
        _config.load()
    return _config
