#!/usr/bin/env python3
"""
性能监控和指标收集模块
"""

import time
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import deque
from pathlib import Path

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_mb: float
    disk_free_mb: float

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    component: str
    operation: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryMetrics:
    """记忆系统指标"""
    timestamp: datetime
    total_memories: int
    memories_by_layer: Dict[int, int]
    total_edges: int
    cache_hit_rate: float
    retrieval_time_ms: float
    storage_time_ms: float

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.system_metrics_history = deque(maxlen=max_history)
        self.performance_metrics_history = deque(maxlen=max_history)
        self.memory_metrics_history = deque(maxlen=max_history)
        
        self.start_time = datetime.now()
        self.component_timers = {}
    
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                disk_used_mb=disk.used / (1024 * 1024),
                disk_free_mb=disk.free / (1024 * 1024)
            )
            
            self.system_metrics_history.append(metrics)
            return metrics
        
        except Exception as e:
            # 回退到简单指标收集
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_used_mb=0.0,
                disk_free_mb=0.0
            )
    
    def start_timer(self, component: str, operation: str):
        """开始计时"""
        key = f"{component}.{operation}"
        self.component_timers[key] = time.time()
    
    def stop_timer(self, component: str, operation: str, success: bool = True, 
                   error_message: Optional[str] = None, **kwargs) -> PerformanceMetrics:
        """停止计时并记录性能指标"""
        key = f"{component}.{operation}"
        start_time = self.component_timers.pop(key, None)
        
        if start_time is None:
            return None
        
        duration_ms = (time.time() - start_time) * 1000
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            additional_info=kwargs
        )
        
        self.performance_metrics_history.append(metrics)
        return metrics
    
    def record_memory_metrics(self, memex, retrieval_time_ms: float = None, 
                             storage_time_ms: float = None):
        """记录记忆系统指标"""
        try:
            system_status = memex.get_system_status()
            
            # 计算缓存命中率（简化版）
            cache_hit_rate = 0.0
            if hasattr(memex, 'cache_stats'):
                hits = memex.cache_stats.get('hits', 0)
                misses = memex.cache_stats.get('misses', 0)
                if hits + misses > 0:
                    cache_hit_rate = hits / (hits + misses)
            
            metrics = MemoryMetrics(
                timestamp=datetime.now(),
                total_memories=system_status['total_memories'],
                memories_by_layer=system_status['memories_by_layer'],
                total_edges=system_status['total_edges'],
                cache_hit_rate=cache_hit_rate,
                retrieval_time_ms=retrieval_time_ms or 0.0,
                storage_time_ms=storage_time_ms or 0.0
            )
            
            self.memory_metrics_history.append(metrics)
            return metrics
        
        except Exception as e:
            return None
    
    def get_performance_summary(self, component: str = None, 
                               time_window_minutes: int = 60) -> Dict:
        """获取性能摘要"""
        now = datetime.now()
        window_start = now - timedelta(minutes=time_window_minutes)
        
        # 过滤时间窗口内的指标
        if component:
            filtered = [
                m for m in self.performance_metrics_history
                if m.timestamp >= window_start and m.component == component
            ]
        else:
            filtered = [
                m for m in self.performance_metrics_history
                if m.timestamp >= window_start
            ]
        
        if not filtered:
            return {"count": 0, "message": f"无{component if component else ''}性能数据"}
        
        # 计算统计信息
        durations = [m.duration_ms for m in filtered]
        success_count = sum(1 for m in filtered if m.success)
        error_count = len(filtered) - success_count
        
        return {
            "count": len(filtered),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "success_rate": success_count / len(filtered),
            "error_count": error_count,
            "operations_by_component": self._group_by_component(filtered),
            "recent_errors": [
                {"component": m.component, "operation": m.operation, 
                 "error": m.error_message, "timestamp": m.timestamp.isoformat()}
                for m in filtered[-10:] if not m.success
            ]
        }
    
    def _group_by_component(self, metrics: List[PerformanceMetrics]) -> Dict:
        """按组件分组指标"""
        groups = {}
        for metric in metrics:
            if metric.component not in groups:
                groups[metric.component] = {
                    "count": 0,
                    "avg_duration": 0,
                    "success_count": 0
                }
            
            group = groups[metric.component]
            group["count"] += 1
            group["avg_duration"] = (
                (group["avg_duration"] * (group["count"] - 1) + metric.duration_ms) 
                / group["count"]
            )
            if metric.success:
                group["success_count"] += 1
        
        # 计算成功率
        for component, data in groups.items():
            data["success_rate"] = data["success_count"] / data["count"]
        
        return groups
    
    def get_system_health(self) -> Dict:
        """获取系统健康状态"""
        try:
            system_metrics = self.collect_system_metrics()
            
            # 定义健康阈值
            cpu_threshold = 90.0
            memory_threshold = 90.0
            disk_threshold = 90.0
            
            issues = []
            
            if system_metrics.cpu_percent > cpu_threshold:
                issues.append(f"CPU使用率过高: {system_metrics.cpu_percent:.1f}%")
            
            if system_metrics.memory_percent > memory_threshold:
                issues.append(f"内存使用率过高: {system_metrics.memory_percent:.1f}%")
            
            if system_metrics.disk_usage_percent > disk_threshold:
                issues.append(f"磁盘使用率过高: {system_metrics.disk_usage_percent:.1f}%")
            
            # 检查最近的错误
            recent_errors = self.get_performance_summary(time_window_minutes=5)
            if recent_errors.get("error_count", 0) > 10:
                issues.append("短时间内错误过多")
            
            return {
                "healthy": len(issues) == 0,
                "issues": issues,
                "system_metrics": asdict(system_metrics),
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "issues": [f"无法获取系统健康状态: {str(e)}"],
                "error": str(e)
            }
    
    def save_metrics_to_file(self, file_path: str):
        """保存指标到文件"""
        try:
            data = {
                "system_metrics": [asdict(m) for m in self.system_metrics_history],
                "performance_metrics": [asdict(m) for m in self.performance_metrics_history],
                "memory_metrics": [asdict(m) for m in self.memory_metrics_history],
                "export_time": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
        
        except Exception as e:
            return False
    
    def reset_metrics(self):
        """重置指标"""
        self.system_metrics_history.clear()
        self.performance_metrics_history.clear()
        self.memory_metrics_history.clear()
        self.component_timers.clear()
        self.start_time = datetime.now()

# 全局监控器实例
performance_monitor = PerformanceMonitor()