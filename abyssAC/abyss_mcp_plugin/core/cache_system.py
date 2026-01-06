#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存系统 - 多种缓存策略实现

提供TTL缓存、LRU缓存和LFU缓存等多种缓存策略。
"""

import time
import threading
from collections import OrderedDict, defaultdict, Counter
from typing import Any, Optional, Dict, List, Tuple, Hashable, Callable
from abc import ABC, abstractmethod


class CacheInterface(ABC):
    """缓存接口"""
    
    @abstractmethod
    def get(self, key: Hashable) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    def put(self, key: Hashable, value: Any):
        """设置缓存值"""
        pass
    
    @abstractmethod
    def delete(self, key: Hashable) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空缓存"""
        pass
    
    @abstractmethod
    def __len__(self) -> int:
        """返回缓存大小"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        pass


class TTLCache(CacheInterface):
    """TTL缓存 - 带过期时间的缓存"""
    
    def __init__(self, maxsize: int = 100, ttl: int = 300):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: Hashable) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                # 检查是否过期
                timestamp = self._timestamps.get(key, 0)
                if time.time() - timestamp < self.ttl:
                    # 移到末尾（LRU）
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return self._cache[key]
                else:
                    # 过期，删除
                    self._delete_key(key)
                    self._misses += 1
            else:
                self._misses += 1
            
            return None
    
    def put(self, key: Hashable, value: Any):
        """设置缓存值"""
        with self._lock:
            current_time = time.time()
            
            # 如果已存在，更新
            if key in self._cache:
                self._cache[key] = value
                self._timestamps[key] = current_time
                self._cache.move_to_end(key)
                return
            
            # 检查大小限制
            if len(self._cache) >= self.maxsize:
                # 删除最旧的
                oldest_key = next(iter(self._cache))
                self._delete_key(oldest_key)
            
            # 添加新值
            self._cache[key] = value
            self._timestamps[key] = current_time
    
    def delete(self, key: Hashable) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                self._delete_key(key)
                return True
            return False
    
    def _delete_key(self, key: Hashable):
        """删除键"""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0
    
    def __len__(self) -> int:
        """返回缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'maxsize': self.maxsize,
                'ttl': self.ttl,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate_percent': round(hit_rate, 2),
                'entries': list(self._cache.keys())[:10]  # 只显示前10个
            }


class LRUCache(CacheInterface):
    """LRU缓存 - 最近最少使用缓存"""
    
    def __init__(self, maxsize: int = 100):
        self.maxsize = maxsize
        self._cache = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: Hashable) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                # 移到末尾
                self._cache.move_to_end(key)
                self._hits += 1
                return self._cache[key]
            else:
                self._misses += 1
                return None
    
    def put(self, key: Hashable, value: Any):
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                # 更新并移到末尾
                self._cache[key] = value
                self._cache.move_to_end(key)
            else:
                # 检查大小限制
                if len(self._cache) >= self.maxsize:
                    # 删除最旧的
                    self._cache.popitem(last=False)
                
                # 添加新值
                self._cache[key] = value
    
    def delete(self, key: Hashable) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def __len__(self) -> int:
        """返回缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def keys(self) -> List[Hashable]:
        """返回所有键"""
        with self._lock:
            return list(self._cache.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'maxsize': self.maxsize,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate_percent': round(hit_rate, 2),
                'entries': list(self._cache.keys())[:10]
            }


class LFUCache(CacheInterface):
    """LFU缓存 - 最不经常使用缓存"""
    
    def __init__(self, maxsize: int = 100):
        self.maxsize = maxsize
        self._cache = {}
        self._freq = Counter()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: Hashable) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                self._freq[key] += 1
                self._hits += 1
                return self._cache[key]
            else:
                self._misses += 1
                return None
    
    def put(self, key: Hashable, value: Any):
        """设置缓存值"""
        with self._lock:
            if key in self._cache:
                self._cache[key] = value
                self._freq[key] += 1
                return
            
            # 检查大小限制
            if len(self._cache) >= self.maxsize:
                # 删除使用频率最低的
                min_freq = min(self._freq.values())
                least_used = [k for k, v in self._freq.items() if v == min_freq]
                
                if least_used:
                    key_to_remove = least_used[0]
                    del self._cache[key_to_remove]
                    del self._freq[key_to_remove]
            
            # 添加新值
            self._cache[key] = value
            self._freq[key] = 1
    
    def delete(self, key: Hashable) -> bool:
        """删除缓存值"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._freq[key]
                return True
            return False
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._freq.clear()
            self._hits = 0
            self._misses = 0
    
    def __len__(self) -> int:
        """返回缓存大小"""
        with self._lock:
            return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            
            return {
                'size': len(self._cache),
                'maxsize': self.maxsize,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate_percent': round(hit_rate, 2),
                'frequency_distribution': dict(self._freq.most_common(10))
            }


class MultiTierCache(CacheInterface):
    """多级缓存 - 结合多种缓存策略"""
    
    def __init__(self, 
                 l1_size: int = 100,  # L1: 高频访问
                 l2_size: int = 500,  # L2: 中频访问
                 l3_size: int = 1000, # L3: 低频访问
                 ttl: int = 300):
        self.l1 = LRUCache(l1_size)  # L1: LRU
        self.l2 = TTLCache(l2_size, ttl)  # L2: TTL
        self.l3 = LFUCache(l3_size)  # L3: LFU
        
        self._lock = threading.RLock()
        self._promotions = 0
        self._demotions = 0
    
    def get(self, key: Hashable) -> Optional[Any]:
        """获取缓存值（多级查找）"""
        with self._lock:
            # L1 -> L2 -> L3
            value = self.l1.get(key)
            if value is not None:
                return value
            
            value = self.l2.get(key)
            if value is not None:
                # 提升到L1
                self._promote_to_l1(key, value)
                return value
            
            value = self.l3.get(key)
            if value is not None:
                # 提升到L2
                self._promote_to_l2(key, value)
                return value
            
            return None
    
    def put(self, key: Hashable, value: Any):
        """设置缓存值"""
        with self._lock:
            # 先尝试L1
            if len(self.l1) < self.l1.maxsize:
                self.l1.put(key, value)
            # 然后L2
            elif len(self.l2) < self.l2.maxsize:
                self.l2.put(key, value)
            # 最后L3
            else:
                self.l3.put(key, value)
    
    def _promote_to_l1(self, key: Hashable, value: Any):
        """提升到L1缓存"""
        if len(self.l1) >= self.l1.maxsize:
            # 从L1驱逐到L2
            l1_keys = list(self.l1.keys())
            if l1_keys:
                victim_key = l1_keys[0]
                victim_value = self.l1.get(victim_key)
                if victim_value is not None:
                    self.l2.put(victim_key, victim_value)
                    self._demotions += 1
        
        self.l1.put(key, value)
        self._promotions += 1
    
    def _promote_to_l2(self, key: Hashable, value: Any):
        """提升到L2缓存"""
        if len(self.l2) >= self.l2.maxsize:
            # 从L2驱逐到L3
            l2_stats = self.l2.get_stats()
            if 'entries' in l2_stats and l2_stats['entries']:
                victim_key = l2_stats['entries'][0]
                victim_value = self.l2.get(victim_key)
                if victim_value is not None:
                    self.l3.put(victim_key, victim_value)
                    self._demotions += 1
        
        self.l2.put(key, value)
        self._promotions += 1
    
    def delete(self, key: Hashable) -> bool:
        """删除缓存值"""
        with self._lock:
            return (self.l1.delete(key) or 
                   self.l2.delete(key) or 
                   self.l3.delete(key))
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self.l1.clear()
            self.l2.clear()
            self.l3.clear()
            self._promotions = 0
            self._demotions = 0
    
    def __len__(self) -> int:
        """返回缓存大小"""
        with self._lock:
            return len(self.l1) + len(self.l2) + len(self.l3)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            l1_stats = self.l1.get_stats()
            l2_stats = self.l2.get_stats()
            l3_stats = self.l3.get_stats()
            
            total_hits = l1_stats['hits'] + l2_stats['hits'] + l3_stats['hits']
            total_misses = l1_stats['misses'] + l2_stats['misses'] + l3_stats['misses']
            total = total_hits + total_misses
            
            overall_hit_rate = (total_hits / total * 100) if total > 0 else 0
            
            return {
                'total_size': len(self),
                'l1_stats': l1_stats,
                'l2_stats': l2_stats,
                'l3_stats': l3_stats,
                'total_hits': total_hits,
                'total_misses': total_misses,
                'overall_hit_rate_percent': round(overall_hit_rate, 2),
                'promotions': self._promotions,
                'demotions': self._demotions
            }


class CacheManager:
    """缓存管理器 - 统一管理多种缓存"""
    
    def __init__(self):
        self._caches = {}
        self._lock = threading.RLock()
    
    def create_cache(self, name: str, cache_type: str = 'lru', **kwargs) -> CacheInterface:
        """创建缓存"""
        with self._lock:
            if cache_type == 'ttl':
                cache = TTLCache(**kwargs)
            elif cache_type == 'lfu':
                cache = LFUCache(**kwargs)
            elif cache_type == 'multitier':
                cache = MultiTierCache(**kwargs)
            else:  # 默认LRU
                cache = LRUCache(**kwargs)
            
            self._caches[name] = cache
            return cache
    
    def get_cache(self, name: str) -> Optional[CacheInterface]:
        """获取缓存"""
        with self._lock:
            return self._caches.get(name)
    
    def delete_cache(self, name: str) -> bool:
        """删除缓存"""
        with self._lock:
            if name in self._caches:
                del self._caches[name]
                return True
            return False
    
    def clear_all(self):
        """清空所有缓存"""
        with self._lock:
            for cache in self._caches.values():
                cache.clear()
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存的统计"""
        with self._lock:
            stats = {}
            for name, cache in self._caches.items():
                stats[name] = cache.get_stats()
            return stats
    
    def cleanup_expired(self):
        """清理过期缓存"""
        with self._lock:
            for cache in self._caches.values():
                if hasattr(cache, '_cache') and hasattr(cache, '_timestamps'):
                    # TTL缓存，需要清理过期项
                    current_time = time.time()
                    expired_keys = []
                    
                    for key, timestamp in cache._timestamps.items():
                        if current_time - timestamp >= cache.ttl:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        cache._delete_key(key)


# 全局缓存管理器实例
cache_manager = CacheManager()