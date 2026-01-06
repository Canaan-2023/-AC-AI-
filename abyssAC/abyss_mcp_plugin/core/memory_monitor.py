#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存监控器 - 无外部依赖的内存监测

使用Python标准库实现内存使用监控，无需安装psutil等外部依赖。
"""

import os
import sys
import gc
import threading
import time
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from pathlib import Path


class MemoryMonitor:
    """
    内存监控器 - 无外部依赖
    
    通过多种方式监控Python进程的内存使用情况：
    1. 读取/proc文件系统（Linux系统）
    2. 使用resource模块（Unix系统）
    3. 通过对象统计估算
    4. GC统计信息
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._history = []
        self._max_history_size = 100
        self._alerts = []
        self._callbacks = []
        
        # 内存阈值（MB）
        self._warning_threshold = 400  # 警告阈值
        self._critical_threshold = 500  # 严重阈值
        
        # 启动监控线程
        self._monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self, interval: int = 10):
        """启动内存监控"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(interval,), 
            daemon=True
        )
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """停止内存监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _monitor_loop(self, interval: int):
        """监控循环"""
        while self._monitoring:
            try:
                # 获取当前内存使用
                memory_info = self.get_memory_info()
                
                # 记录历史
                self._record_memory_snapshot(memory_info)
                
                # 检查阈值
                self._check_thresholds(memory_info)
                
                # 触发回调
                self._trigger_callbacks(memory_info)
                
            except Exception as e:
                # 静默处理监控错误，避免影响主程序
                pass
            
            time.sleep(interval)
    
    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存信息"""
        with self._lock:
            info = {
                'timestamp': time.time(),
                'python_version': sys.version,
                'platform': sys.platform
            }
            
            # 尝试多种方法获取内存信息
            info.update(self._get_memory_from_proc())
            info.update(self._get_memory_from_resource())
            info.update(self._get_memory_from_gc())
            info.update(self._get_object_stats())
            
            return info
    
    def _get_memory_from_proc(self) -> Dict[str, Any]:
        """从/proc文件系统获取内存信息（Linux）"""
        info = {}
        
        try:
            # 读取进程状态
            status_path = f'/proc/{os.getpid()}/status'
            if os.path.exists(status_path):
                with open(status_path, 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            # 常驻内存大小（KB）
                            info['resident_memory_kb'] = int(line.split()[1])
                            info['resident_memory_mb'] = info['resident_memory_kb'] / 1024
                        elif line.startswith('VmSize:'):
                            # 虚拟内存大小（KB）
                            info['virtual_memory_kb'] = int(line.split()[1])
                            info['virtual_memory_mb'] = info['virtual_memory_kb'] / 1024
                        elif line.startswith('VmPeak:'):
                            # 峰值虚拟内存（KB）
                            info['peak_virtual_memory_kb'] = int(line.split()[1])
                            info['peak_virtual_memory_mb'] = info['peak_virtual_memory_kb'] / 1024
        except (IOError, OSError, ValueError):
            # 文件不存在或无法读取
            pass
        
        return info
    
    def _get_memory_from_resource(self) -> Dict[str, Any]:
        """从resource模块获取内存信息（Unix）"""
        info = {}
        
        try:
            import resource
            
            # 获取当前内存使用
            usage = resource.getrusage(resource.RUSAGE_SELF)
            
            # ru_maxrss: 最大常驻内存大小（不同系统单位不同）
            maxrss = usage.ru_maxrss
            if sys.platform == 'darwin':  # macOS
                info['maxrss_mb'] = maxrss / (1024 * 1024)
            else:  # Linux和其他Unix系统
                info['maxrss_mb'] = maxrss / 1024
            
            info['ru_utime'] = usage.ru_utime  # 用户CPU时间
            info['ru_stime'] = usage.ru_stime  # 系统CPU时间
            info['ru_nswap'] = usage.ru_nswap  # 交换次数
            info['ru_majflt'] = usage.ru_majflt  # 页错误次数
            
        except (ImportError, AttributeError):
            # resource模块不可用
            pass
        
        return info
    
    def _get_memory_from_gc(self) -> Dict[str, Any]:
        """从GC获取内存统计"""
        info = {
            'gc_enabled': gc.isenabled(),
            'gc_thresholds': gc.get_threshold(),
            'gc_counts': gc.get_count(),
            'gc_garbage_len': len(gc.garbage)
        }
        
        # 获取对象代信息
        try:
            info['gc_stats'] = gc.get_stats()
        except AttributeError:
            # Python 3.3以下版本没有get_stats
            pass
        
        return info
    
    def _get_object_stats(self) -> Dict[str, Any]:
        """获取对象统计"""
        info = {}
        
        try:
            # 统计不同类型对象的数量
            type_counts = defaultdict(int)
            size_estimates = defaultdict(int)
            
            for obj in gc.get_objects():
                obj_type = type(obj).__name__
                type_counts[obj_type] += 1
                
                # 估算对象大小（粗略估计）
                if hasattr(obj, '__sizeof__'):
                    size_estimates[obj_type] += obj.__sizeof__()
                else:
                    # 默认估算
                    size_estimates[obj_type] += 64  # 假设平均64字节
            
            # 获取最常见的对象类型
            most_common = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            
            info.update({
                'total_objects': len(gc.get_objects()),
                'type_counts': dict(type_counts),
                'most_common_types': most_common,
                'estimated_total_size': sum(size_estimates.values()),
                'size_estimates': dict(size_estimates)
            })
            
        except Exception:
            # 对象统计失败
            pass
        
        return info
    
    def _record_memory_snapshot(self, memory_info: Dict[str, Any]):
        """记录内存快照"""
        with self._lock:
            snapshot = {
                'timestamp': time.time(),
                'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
                'memory_info': memory_info
            }
            
            self._history.append(snapshot)
            
            # 限制历史大小
            if len(self._history) > self._max_history_size:
                self._history.pop(0)
    
    def _check_thresholds(self, memory_info: Dict[str, Any]):
        """检查内存阈值"""
        # 获取当前内存使用
        current_mb = 0
        
        if 'resident_memory_mb' in memory_info:
            current_mb = memory_info['resident_memory_mb']
        elif 'maxrss_mb' in memory_info:
            current_mb = memory_info['maxrss_mb']
        
        if current_mb <= 0:
            return
        
        # 检查警告阈值
        if current_mb > self._critical_threshold:
            alert = {
                'level': 'CRITICAL',
                'message': f'内存使用严重超标: {current_mb:.1f}MB > {self._critical_threshold}MB',
                'timestamp': time.time()
            }
            self._alerts.append(alert)
            
        elif current_mb > self._warning_threshold:
            alert = {
                'level': 'WARNING',
                'message': f'内存使用较高: {current_mb:.1f}MB > {self._warning_threshold}MB',
                'timestamp': time.time()
            }
            self._alerts.append(alert)
    
    def _trigger_callbacks(self, memory_info: Dict[str, Any]):
        """触发内存监控回调"""
        for callback in self._callbacks:
            try:
                callback(memory_info)
            except Exception:
                # 回调失败不应影响监控
                pass
    
    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加监控回调"""
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """移除监控回调"""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def get_memory_history(self, limit: int = 50) -> list:
        """获取内存使用历史"""
        with self._lock:
            return self._history[-limit:] if self._history else []
    
    def get_current_memory_usage(self) -> Dict[str, Any]:
        """获取当前内存使用情况"""
        info = self.get_memory_info()
        
        # 提取关键指标
        usage = {
            'timestamp': info['timestamp'],
            'datetime': info.get('datetime', time.strftime('%Y-%m-%d %H:%M:%S'))
        }
        
        # 优先使用常驻内存
        if 'resident_memory_mb' in info:
            usage['memory_mb'] = info['resident_memory_mb']
        elif 'maxrss_mb' in info:
            usage['memory_mb'] = info['maxrss_mb']
        else:
            # 估算内存使用
            estimated = info.get('estimated_total_size', 0) / (1024 * 1024)
            usage['memory_mb'] = estimated
            usage['estimated'] = True
        
        # 添加GC信息
        if 'gc_counts' in info:
            usage['gc_generation_counts'] = info['gc_counts']
        
        return usage
    
    def force_gc(self) -> Dict[str, Any]:
        """强制垃圾回收"""
        before = self.get_current_memory_usage()
        
        # 执行垃圾回收
        collected = gc.collect()
        
        after = self.get_current_memory_usage()
        
        return {
            'before_memory_mb': before.get('memory_mb', 0),
            'after_memory_mb': after.get('memory_mb', 0),
            'freed_mb': before.get('memory_mb', 0) - after.get('memory_mb', 0),
            'collected_objects': collected,
            'timestamp': time.time()
        }
    
    def set_thresholds(self, warning_mb: int, critical_mb: int):
        """设置内存阈值"""
        self._warning_threshold = warning_mb
        self._critical_threshold = critical_mb
    
    def get_alerts(self, clear: bool = True) -> list:
        """获取内存警报"""
        with self._lock:
            alerts = list(self._alerts)
            if clear:
                self._alerts.clear()
            return alerts
    
    def get_memory_report(self) -> Dict[str, Any]:
        """获取内存使用报告"""
        current = self.get_current_memory_usage()
        history = self.get_memory_history(20)
        alerts = self.get_alerts(clear=False)
        
        # 计算统计数据
        if history:
            memory_values = [h['memory_info'].get('resident_memory_mb', 
                           h['memory_info'].get('maxrss_mb', 0)) for h in history]
            memory_values = [v for v in memory_values if v > 0]
            
            if memory_values:
                avg_memory = sum(memory_values) / len(memory_values)
                max_memory = max(memory_values)
                min_memory = min(memory_values)
            else:
                avg_memory = max_memory = min_memory = 0
        else:
            avg_memory = max_memory = min_memory = current.get('memory_mb', 0)
        
        return {
            'current': current,
            'statistics': {
                'average_mb': round(avg_memory, 2),
                'maximum_mb': round(max_memory, 2),
                'minimum_mb': round(min_memory, 2)
            },
            'alerts': alerts,
            'history_count': len(history),
            'gc_enabled': gc.isenabled(),
            'gc_thresholds': gc.get_threshold()
        }


# 全局内存监控实例
memory_monitor = MemoryMonitor()