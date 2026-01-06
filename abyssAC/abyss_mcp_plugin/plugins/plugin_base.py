#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件基类 - 定义插件接口
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


class PluginType(Enum):
    """插件类型"""
    COGNITIVE = "cognitive"  # 认知插件
    MEMORY = "memory"        # 记忆插件
    DICTIONARY = "dictionary" # 字典插件
    API = "api"              # API插件
    MONITOR = "monitor"      # 监控插件
    INTEGRATION = "integration"  # 集成插件


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    type: PluginType
    dependencies: List[str]
    config_schema: Optional[Dict[str, Any]] = None
    enabled: bool = True


class PluginBase(ABC):
    """插件基类"""
    
    def __init__(self, info: PluginInfo):
        self.info = info
        self.enabled = info.enabled
        self.config = {}
    
    @abstractmethod
    def initialize(self, kernel, config: Dict[str, Any] = None):
        """初始化插件"""
        pass
    
    @abstractmethod
    def cleanup(self):
        """清理插件资源"""
        pass
    
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        return self.info
    
    def is_enabled(self) -> bool:
        """检查插件是否启用"""
        return self.enabled
    
    def enable(self):
        """启用插件"""
        self.enabled = True
    
    def disable(self):
        """禁用插件"""
        self.enabled = False
    
    def update_config(self, config: Dict[str, Any]):
        """更新插件配置"""
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取插件配置"""
        return self.config.copy()


class CognitivePlugin(PluginBase):
    """认知插件基类"""
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        if info.type != PluginType.COGNITIVE:
            raise ValueError(f"Plugin type must be {PluginType.COGNITIVE}")
    
    @abstractmethod
    def process_activation(self, text: str, activations: Dict[str, float]) -> Dict[str, float]:
        """处理认知激活"""
        pass
    
    @abstractmethod
    def enhance_tokenization(self, tokens: List[str]) -> List[str]:
        """增强分词结果"""
        pass


class MemoryPlugin(PluginBase):
    """记忆插件基类"""
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        if info.type != PluginType.MEMORY:
            raise ValueError(f"Plugin type must be {PluginType.MEMORY}")
    
    @abstractmethod
    def before_memory_creation(self, content: str, metadata: Dict[str, Any]) -> tuple:
        """记忆创建前处理"""
        pass
    
    @abstractmethod
    def after_memory_retrieval(self, memories: List[Any]) -> List[Any]:
        """记忆检索后处理"""
        pass


class DictionaryPlugin(PluginBase):
    """字典插件基类"""
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        if info.type != PluginType.DICTIONARY:
            raise ValueError(f"Plugin type must be {PluginType.DICTIONARY}")
    
    @abstractmethod
    def before_word_addition(self, word: str) -> str:
        """词添加前处理"""
        pass
    
    @abstractmethod
    def enhance_search(self, query: str, results: List[str]) -> List[str]:
        """增强搜索结果"""
        pass


class APIPlugin(PluginBase):
    """API插件基类"""
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        if info.type != PluginType.API:
            raise ValueError(f"Plugin type must be {PluginType.API}")
    
    @abstractmethod
    def register_routes(self, router):
        """注册API路由"""
        pass
    
    @abstractmethod
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求"""
        pass


class MonitorPlugin(PluginBase):
    """监控插件基类"""
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        if info.type != PluginType.MONITOR:
            raise ValueError(f"Plugin type must be {PluginType.MONITOR}")
    
    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """收集指标"""
        pass
    
    @abstractmethod
    def process_alert(self, alert: Dict[str, Any]):
        """处理警报"""
        pass


class IntegrationPlugin(PluginBase):
    """集成插件基类"""
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        if info.type != PluginType.INTEGRATION:
            raise ValueError(f"Plugin type must be {PluginType.INTEGRATION}")
    
    @abstractmethod
    def import_data(self, source: str, data: Any) -> bool:
        """导入数据"""
        pass
    
    @abstractmethod
    def export_data(self, format: str) -> Any:
        """导出数据"""
        pass