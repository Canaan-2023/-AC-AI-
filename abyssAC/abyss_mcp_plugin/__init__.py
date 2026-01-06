#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议 MCP 插件系统

一个完整的模型-控制器-插件架构，用于构建可扩展的认知计算系统。

主要特性:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 三层架构: Model-Controller-Plugin 分离
✅ 反向索引系统: 增强记忆检索性能
✅ 无外部依赖: 纯Python标准库实现
✅ 完整API接口: RESTful API支持
✅ 插件系统: 动态加载和扩展
✅ 内存监测: 内置内存使用监控
✅ 并发安全: 完整的线程安全保护
✅ 持久化: 自动状态保存和恢复
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

作者: AbyssAC Protocol Team
版本: 4.0.0 (MCP架构版)
依赖: 无外部依赖，纯Python标准库
"""

__version__ = "4.0.0"
__author__ = "AbyssAC Protocol Team"
__description__ = "渊协议 MCP 插件系统 - 模型-控制器-插件架构"

from .core.abyss_kernel import AbyssKernel
from .models.memory_system import MemorySystem
from .controllers.api_controller import APIController
from .plugins.plugin_manager import PluginManager

__all__ = [
    "AbyssKernel",
    "MemorySystem", 
    "APIController",
    "PluginManager"
]