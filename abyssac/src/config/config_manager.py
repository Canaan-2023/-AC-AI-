"""配置管理模块"""

import os
import json
from typing import Any, Dict, Optional

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化配置管理器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.default_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'paths': {
                'nngrootpath': 'storage/nng/',
                'memoryrootpath': 'storage/Y层记忆库/',
                'temp_path': 'temp/',
                'navlogpath': 'X层/navigation_logs/',
                'systemlogpath': 'logs/'
            },
            'system': {
                'system_time': '2026-02-20 10:00:00',
                'timestamp_format': 'YYYY-MM-DD HH:MM:SS',
                'max_memory_size': 1048576000,
                'max_nng_nodes': 10000,
                'idle_threshold': 300
            },
            'llm': {
                'model_name': 'ollama',
                'api_endpoint': 'http://localhost:11434/api/generate',
                'max_tokens': 4096,
                'temperature': 0.7,
                'timeout': 30,
                'retry_count': 3
            },
            'sandbox': {
                'nng': {
                    'max_depth': 5,
                    'max_nodes': 1000
                },
                'memory': {
                    'max_files': 100,
                    'max_size': 10485760
                },
                'context': {
                    'max_length': 8192,
                    'compression_threshold': 4096
                }
            },
            'security': {
                'access_control': {
                    'enabled': True,
                    'default_permission': 'read'
                }
            },
            'confidence': {
                'thresholds': {
                    'high': 0.90,
                    'medium_high': 0.70,
                    'medium': 0.50,
                    'medium_low': 0.30,
                    'low': 0.00
                },
                'strategies': {
                    'high': 'direct_use',
                    'medium_high': 'use_with_other_info',
                    'medium': 'use_after_verification',
                    'medium_low': 'use_with_caution',
                    'low': 'do_not_use'
                }
            }
        }
    
    def get_config(self, key: str, default: Optional[Any] = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的路径
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            # 分割键路径
            keys = key.split('.')
            value = self.config
            
            # 遍历键路径
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    # 如果配置不存在，尝试从默认配置获取
                    value = self.default_config
                    for k in keys:
                        if isinstance(value, dict) and k in value:
                            value = value[k]
                        else:
                            return default
                    return value
            
            return value
        except Exception:
            return default
    
    def set_config(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            是否设置成功
        """
        try:
            # 分割键路径
            keys = key.split('.')
            config = self.config
            
            # 遍历键路径，创建不存在的层级
            for i, k in enumerate(keys[:-1]):
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            # 设置值
            config[keys[-1]] = value
            return True
        except Exception:
            return False
    
    def reload_config(self) -> bool:
        """重新加载配置
        
        Returns:
            是否加载成功
        """
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config.json'
            )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            return True
        except Exception:
            return False
    
    def validate_config(self) -> bool:
        """验证配置
        
        Returns:
            验证结果
        """
        try:
            # 验证必要的配置项
            required_keys = [
                'paths.nngrootpath',
                'paths.memoryrootpath',
                'llm.api_endpoint',
                'llm.model_name'
            ]
            
            for key in required_keys:
                if self.get_config(key) is None:
                    return False
            
            return True
        except Exception:
            return False
    
    def get_confidence_thresholds(self) -> Dict[str, float]:
        """获取置信度阈值配置
        
        Returns:
            置信度阈值配置字典
        """
        return self.get_config('confidence.thresholds', {
            'high': 0.90,
            'medium_high': 0.70,
            'medium': 0.50,
            'medium_low': 0.30,
            'low': 0.00
        })
    
    def set_confidence_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """设置置信度阈值配置
        
        Args:
            thresholds: 置信度阈值配置字典
            
        Returns:
            是否设置成功
        """
        return self.set_config('confidence.thresholds', thresholds)
    
    def validate_confidence_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """验证置信度阈值配置
        
        Args:
            thresholds: 置信度阈值配置字典
            
        Returns:
            验证结果
        """
        try:
            required_thresholds = ['high', 'medium_high', 'medium', 'medium_low', 'low']
            
            for key in required_thresholds:
                if key not in thresholds:
                    return False
                
                value = thresholds[key]
                if not isinstance(value, (int, float)) or value < 0 or value > 1:
                    return False
            
            return True
        except Exception:
            return False