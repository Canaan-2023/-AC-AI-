#!/usr/bin/env python3
"""
配置模块
"""

from .config_manager import ConfigManager, SystemConfig

# 全局配置管理器实例
config_manager = ConfigManager()

__all__ = ["config_manager", "SystemConfig", "ConfigManager"]