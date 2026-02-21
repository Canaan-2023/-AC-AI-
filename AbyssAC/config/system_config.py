"""
AbyssAC System Configuration Module
系统配置模块 - 所有路径、计数器、阈值配置
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any
from datetime import datetime


@dataclass
class PathConfig:
    """路径配置"""
    nng_root_path: str = "storage/nng/"
    memory_root_path: str = "storage/Y层记忆库/"
    temp_path: str = "temp/"
    nav_log_path: str = "X层/navigation_logs/"
    system_log_path: str = "logs/"
    ai_dev_space_path: str = "storage/AI开发空间/"
    sandbox_path: str = "storage/沙箱/"
    
    def __post_init__(self):
        # 确保所有路径都存在
        for attr_name in dir(self):
            if attr_name.endswith('_path') and not attr_name.startswith('_'):
                path = getattr(self, attr_name)
                os.makedirs(path, exist_ok=True)


@dataclass
class CounterConfig:
    """计数器配置"""
    memory_counter: int = 1
    nng_id_counter: Dict[str, int] = field(default_factory=dict)
    task_counter: int = 1
    nav_fail_counter: int = 0
    
    def get_next_memory_id(self) -> int:
        """获取下一个记忆ID"""
        current = self.memory_counter
        self.memory_counter += 1
        return current
    
    def get_next_nng_child_id(self, parent_id: str) -> str:
        """获取下一个NNG子节点ID"""
        if parent_id not in self.nng_id_counter:
            self.nng_id_counter[parent_id] = 1
        else:
            self.nng_id_counter[parent_id] += 1
        return f"{parent_id}.{self.nng_id_counter[parent_id]}"


@dataclass
class TimeConfig:
    """时间配置"""
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"
    idle_check_interval: int = 300  # 5分钟
    daily_maintenance_time: str = "02:00:00"
    nav_timeout_threshold: int = 30  # 30秒
    
    def get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        return datetime.now().strftime(self.timestamp_format)
    
    def get_current_date_path(self) -> tuple:
        """获取当前日期路径 (year, month, day)"""
        now = datetime.now()
        return (now.strftime("%Y"), now.strftime("%m"), now.strftime("%d"))


@dataclass
class RuntimeConfig:
    """运行时参数配置"""
    max_nav_depth: int = 10
    work_memory_threshold: int = 20
    idle_time_threshold: int = 300  # 5分钟
    fail_count_threshold: int = 5
    dmn_timeout: int = 300  # 5分钟
    confidence_threshold_high: float = 0.8
    confidence_threshold_medium: float = 0.5


@dataclass
class LLMConfig:
    """LLM配置"""
    api_base: str = "http://localhost:11434"
    model_name: str = "llama3.1"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


class SystemConfig:
    """系统主配置类"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.paths = PathConfig()
        self.counters = CounterConfig()
        self.time = TimeConfig()
        self.runtime = RuntimeConfig()
        self.llm = LLMConfig()
        
        # 确保基础目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有必要目录存在"""
        dirs = [
            self.paths.nng_root_path,
            self.paths.memory_root_path,
            f"{self.paths.memory_root_path}/元认知记忆",
            f"{self.paths.memory_root_path}/高阶整合记忆",
            f"{self.paths.memory_root_path}/分类记忆/高价值",
            f"{self.paths.memory_root_path}/分类记忆/中价值",
            f"{self.paths.memory_root_path}/分类记忆/低价值",
            f"{self.paths.memory_root_path}/工作记忆",
            self.paths.temp_path,
            self.paths.nav_log_path,
            self.paths.system_log_path,
            self.paths.ai_dev_space_path,
            self.paths.sandbox_path,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    
    def get_placeholder_values(self) -> Dict[str, Any]:
        """获取所有占位符的当前值"""
        year, month, day = self.time.get_current_date_path()
        return {
            "{nng_root_path}": self.paths.nng_root_path,
            "{memory_root_path}": self.paths.memory_root_path,
            "{temp_path}": self.paths.temp_path,
            "{nav_log_path}": self.paths.nav_log_path,
            "{system_log_path}": self.paths.system_log_path,
            "{current_timestamp}": self.time.get_current_timestamp(),
            "{memory_counter}": self.counters.memory_counter,
            "{max_nav_depth}": self.runtime.max_nav_depth,
            "{work_memory_threshold}": self.runtime.work_memory_threshold,
            "{idle_time_threshold}": self.runtime.idle_time_threshold,
            "{fail_count_threshold}": self.runtime.fail_count_threshold,
            "{year}": year,
            "{month}": month,
            "{day}": day,
        }
    
    def replace_placeholders(self, text: str) -> str:
        """替换文本中的占位符"""
        values = self.get_placeholder_values()
        for placeholder, value in values.items():
            text = text.replace(placeholder, str(value))
        return text


# 全局配置实例
_config_instance = None


def get_config() -> SystemConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SystemConfig()
    return _config_instance


def init_config(base_path: str = ".") -> SystemConfig:
    """初始化配置"""
    global _config_instance
    _config_instance = SystemConfig(base_path)
    return _config_instance
