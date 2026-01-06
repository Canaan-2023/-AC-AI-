#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件系统 - 插件间通信和扩展机制

提供事件驱动的架构，支持插件间的松耦合通信。
"""

import threading
import time
from typing import Dict, List, Any, Callable, Optional, Set
from collections import defaultdict
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


class EventPriority(Enum):
    """事件优先级"""
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


@dataclass
class Event:
    """事件对象"""
    name: str
    data: Dict[str, Any]
    timestamp: float
    source: str
    priority: EventPriority = EventPriority.NORMAL
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class EventHandler(ABC):
    """事件处理器接口"""
    
    @abstractmethod
    def handle_event(self, event: Event):
        """处理事件"""
        pass
    
    @abstractmethod
    def get_subscribed_events(self) -> List[str]:
        """获取订阅的事件列表"""
        pass


class EventSystem:
    """
    事件系统 - 插件间通信核心
    
    支持：
    - 同步和异步事件处理
    - 事件优先级
    - 事件过滤
    - 历史记录
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Tuple[EventHandler, EventPriority]]] = defaultdict(list)
        self._callbacks: Dict[str, List[Tuple[Callable, EventPriority]]] = defaultdict(list)
        self._history: List[Event] = []
        self._lock = threading.RLock()
        self._history_lock = threading.RLock()
        self._max_history_size = 1000
        self._event_counter = 0
        self._counter_lock = threading.Lock()
        
        # 异步处理
        self._async_queue = []
        self._async_thread = None
        self._async_lock = threading.Lock()
        self._async_running = False
        
        # 事件统计
        self._stats = defaultdict(int)
        self._stats_lock = threading.Lock()
    
    def subscribe(self, event_name: str, handler: EventHandler, priority: EventPriority = EventPriority.NORMAL):
        """订阅事件（处理器方式）"""
        with self._lock:
            handlers = self._handlers[event_name]
            
            # 检查是否已订阅
            for h, p in handlers:
                if h == handler:
                    return
            
            # 按优先级插入
            inserted = False
            for i, (h, p) in enumerate(handlers):
                if priority.value < p.value:
                    handlers.insert(i, (handler, priority))
                    inserted = True
                    break
            
            if not inserted:
                handlers.append((handler, priority))
    
    def unsubscribe(self, event_name: str, handler: EventHandler):
        """取消订阅"""
        with self._lock:
            handlers = self._handlers[event_name]
            self._handlers[event_name] = [(h, p) for h, p in handlers if h != handler]
    
    def subscribe_callback(self, event_name: str, callback: Callable[[Event], None], 
                          priority: EventPriority = EventPriority.NORMAL):
        """订阅事件（回调函数方式）"""
        with self._lock:
            callbacks = self._callbacks[event_name]
            
            # 检查是否已订阅
            for c, p in callbacks:
                if c == callback:
                    return
            
            # 按优先级插入
            inserted = False
            for i, (c, p) in enumerate(callbacks):
                if priority.value < p.value:
                    callbacks.insert(i, (callback, priority))
                    inserted = True
                    break
            
            if not inserted:
                callbacks.append((callback, priority))
    
    def unsubscribe_callback(self, event_name: str, callback: Callable[[Event], None]):
        """取消订阅回调"""
        with self._lock:
            callbacks = self._callbacks[event_name]
            self._callbacks[event_name] = [(c, p) for c, p in callbacks if c != callback]
    
    def emit(self, event_name: str, data: Dict[str, Any], source: str = "unknown",
             priority: EventPriority = EventPriority.NORMAL, async_: bool = False) -> Event:
        """发送事件"""
        with self._counter_lock:
            self._event_counter += 1
            event_id = f"{event_name}_{self._event_counter}"
        
        event = Event(
            name=event_name,
            data=data,
            timestamp=time.time(),
            source=source,
            priority=priority
        )
        
        # 记录历史
        self._record_event(event)
        
        # 更新统计
        with self._stats_lock:
            self._stats[event_name] += 1
        
        if async_:
            self._emit_async(event)
        else:
            self._emit_sync(event)
        
        return event
    
    def _emit_sync(self, event: Event):
        """同步发送事件"""
        # 获取处理器
        handlers = []
        with self._lock:
            if event.name in self._handlers:
                handlers.extend(self._handlers[event.name])
        
        # 执行处理器
        for handler, priority in handlers:
            try:
                handler.handle_event(event)
            except Exception as e:
                # 处理器错误不应影响其他处理器
                pass
        
        # 获取回调
        callbacks = []
        with self._lock:
            if event.name in self._callbacks:
                callbacks.extend(self._callbacks[event.name])
        
        # 执行回调
        for callback, priority in callbacks:
            try:
                callback(event)
            except Exception as e:
                # 回调错误不应影响其他回调
                pass
    
    def _emit_async(self, event: Event):
        """异步发送事件"""
        with self._async_lock:
            self._async_queue.append(event)
            
            if not self._async_running:
                self._start_async_processor()
    
    def _start_async_processor(self):
        """启动异步处理器"""
        self._async_running = True
        self._async_thread = threading.Thread(target=self._async_processor, daemon=True)
        self._async_thread.start()
    
    def _async_processor(self):
        """异步事件处理器"""
        while True:
            event = None
            
            with self._async_lock:
                if self._async_queue:
                    event = self._async_queue.pop(0)
                else:
                    self._async_running = False
                    break
            
            if event:
                self._emit_sync(event)
            
            # 短暂休眠，避免CPU占用过高
            time.sleep(0.001)
    
    def _record_event(self, event: Event):
        """记录事件到历史"""
        with self._history_lock:
            self._history.append(event)
            
            if len(self._history) > self._max_history_size:
                self._history.pop(0)
    
    def get_history(self, event_name: Optional[str] = None, 
                   source: Optional[str] = None,
                   limit: int = 100) -> List[Event]:
        """获取事件历史"""
        with self._history_lock:
            filtered_events = []
            
            for event in reversed(self._history):
                if event_name and event.name != event_name:
                    continue
                
                if source and event.source != source:
                    continue
                
                filtered_events.append(event)
                
                if len(filtered_events) >= limit:
                    break
            
            return list(reversed(filtered_events))
    
    def get_stats(self) -> Dict[str, Any]:
        """获取事件统计"""
        with self._stats_lock:
            return {
                'total_events': self._event_counter,
                'event_counts': dict(self._stats),
                'handler_count': sum(len(handlers) for handlers in self._handlers.values()),
                'callback_count': sum(len(callbacks) for callbacks in self._callbacks.values()),
                'history_size': len(self._history),
                'async_queue_size': len(self._async_queue)
            }
    
    def clear_history(self):
        """清空事件历史"""
        with self._history_lock:
            self._history.clear()
    
    def clear_all_subscriptions(self):
        """清空所有订阅"""
        with self._lock:
            self._handlers.clear()
            self._callbacks.clear()
    
    def wait_for_event(self, event_name: str, timeout: float = 10.0) -> Optional[Event]:
        """等待特定事件"""
        result = [None]
        event_received = threading.Event()
        
        def callback(event: Event):
            if event.name == event_name:
                result[0] = event
                event_received.set()
        
        self.subscribe_callback(event_name, callback)
        
        try:
            if event_received.wait(timeout):
                return result[0]
            else:
                return None
        finally:
            self.unsubscribe_callback(event_name, callback)


# 常用事件类型
class SystemEvents:
    """系统事件类型"""
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    CONFIG_CHANGED = "config.changed"
    MEMORY_WARNING = "system.memory_warning"
    MEMORY_CRITICAL = "system.memory_critical"
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    MEMORY_CREATED = "memory.created"
    MEMORY_RETRIEVED = "memory.retrieved"
    COGNITIVE_ACTIVATION = "cognitive.activation"
    FISSION_TRIGGERED = "fission.triggered"
    FISSION_COMPLETED = "fission.completed"


# 全局事件系统实例
event_system = EventSystem()