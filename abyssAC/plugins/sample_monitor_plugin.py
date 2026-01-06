#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例监控插件

展示如何实现一个监控插件来收集系统指标。
"""

import time
from collections import defaultdict
from abyss_mcp_plugin.plugins.plugin_base import MonitorPlugin, PluginInfo, PluginType


class SampleMonitorPlugin(MonitorPlugin):
    """示例监控插件"""
    
    # 插件信息
    PLUGIN_INFO = {
        "name": "SampleMonitor",
        "version": "1.0.0",
        "description": "示例监控插件，收集系统性能指标",
        "author": "AbyssAC Team",
        "type": "monitor",
        "dependencies": []
    }
    
    def __init__(self, info: PluginInfo):
        super().__init__(info)
        self.metrics_history = []
        self.max_history_size = 100
        self.alert_thresholds = {
            'memory_usage_mb': 400,
            'request_rate_per_minute': 100,
            'error_rate_percent': 5
        }
    
    def initialize(self, kernel, config: dict = None):
        """初始化插件"""
        self.kernel = kernel
        if config:
            self.alert_thresholds.update(config.get('thresholds', {}))
        self.logger.info("示例监控插件初始化完成")
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("示例监控插件清理完成")
    
    def collect_metrics(self) -> dict:
        """收集指标"""
        metrics = {
            'timestamp': time.time(),
            'memory_usage': self._get_memory_usage(),
            'cognitive_activations': self._get_cognitive_stats(),
            'dictionary_stats': self._get_dictionary_stats(),
            'memory_stats': self._get_memory_stats(),
            'api_stats': self._get_api_stats()
        }
        
        # 保存历史
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history.pop(0)
        
        # 检查警报
        self._check_alerts(metrics)
        
        return metrics
    
    def _get_memory_usage(self) -> dict:
        """获取内存使用情况"""
        from abyss_mcp_plugin.core.memory_monitor import memory_monitor
        return memory_monitor.get_current_memory_usage()
    
    def _get_cognitive_stats(self) -> dict:
        """获取认知统计"""
        if hasattr(self.kernel, 'cognitive'):
            return self.kernel.cognitive.get_activation_summary()
        return {}
    
    def _get_dictionary_stats(self) -> dict:
        """获取字典统计"""
        if hasattr(self.kernel, 'dict_manager'):
            return self.kernel.dict_manager.get_stats()
        return {}
    
    def _get_memory_stats(self) -> dict:
        """获取记忆统计"""
        if hasattr(self.kernel, 'memory'):
            return self.kernel.memory.get_stats()
        return {}
    
    def _get_api_stats(self) -> dict:
        """获取API统计"""
        if hasattr(self.kernel, 'api_controller'):
            return {
                'request_count': getattr(self.kernel.api_controller, 'request_count', 0),
                'uptime': time.time() - getattr(self.kernel, 'start_time', time.time())
            }
        return {}
    
    def _check_alerts(self, metrics: dict):
        """检查警报条件"""
        alerts = []
        
        # 内存使用警报
        memory_mb = metrics.get('memory_usage', {}).get('memory_mb', 0)
        if memory_mb > self.alert_thresholds['memory_usage_mb']:
            alerts.append({
                'type': 'memory_warning',
                'level': 'warning',
                'message': f"内存使用过高: {memory_mb:.1f}MB",
                'threshold': self.alert_thresholds['memory_usage_mb'],
                'current': memory_mb
            })
        
        # 处理警报
        for alert in alerts:
            self.process_alert(alert)
    
    def process_alert(self, alert: dict):
        """处理警报"""
        self.logger.warning(f"警报触发: {alert['message']}")
        
        # 这里可以添加更多的警报处理逻辑
        # 比如发送邮件、写入日志文件、调用外部服务等
    
    def get_metrics_history(self, limit: int = 10) -> list:
        """获取指标历史"""
        return self.metrics_history[-limit:] if self.metrics_history else []
    
    def get_average_metrics(self, duration_hours: int = 1) -> dict:
        """获取平均指标"""
        if not self.metrics_history:
            return {}
        
        cutoff_time = time.time() - (duration_hours * 3600)
        recent_metrics = [
            m for m in self.metrics_history
            if m['timestamp'] > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # 计算平均值
        avg_metrics = {}
        for key in ['memory_usage', 'cognitive_activations', 'dictionary_stats']:
            values = [m.get(key, {}) for m in recent_metrics]
            if values:
                avg_metrics[key] = self._calculate_average_dict(values)
        
        return avg_metrics
    
    def _calculate_average_dict(self, dict_list: list) -> dict:
        """计算字典的平均值"""
        if not dict_list:
            return {}
        
        result = {}
        for key in dict_list[0].keys():
            values = [d.get(key, 0) for d in dict_list if isinstance(d.get(key, 0), (int, float))]
            if values:
                result[key] = sum(values) / len(values)
        
        return result