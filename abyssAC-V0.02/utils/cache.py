#!/usr/bin/env python3
"""
缓存系统模块
"""

import time
import pickle
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from collections import OrderedDict
from pathlib import Path
import hashlib

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    timestamp: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # Time To Live in seconds
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() > self.timestamp + self.ttl

class LRUCache:
    """LRU（最近最少使用）缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = ttl
        self.cache = OrderedDict()  # key -> CacheEntry
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Any:
        """获取缓存值"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # 检查是否过期
        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None
        
        # 更新访问记录
        entry.access_count += 1
        entry.last_access = time.time()
        
        # 移动到最近使用位置
        self.cache.move_to_end(key)
        
        self.hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """设置缓存值"""
        # 如果缓存已满，移除最旧的条目
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)  # FIFO
        
        # 创建缓存条目
        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )
        
        self.cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "avg_access_count": (
                sum(entry.access_count for entry in self.cache.values()) / len(self.cache)
                if self.cache else 0
            )
        }

class FunctionCache:
    """函数结果缓存装饰器"""
    
    def __init__(self, cache: LRUCache, key_func: Optional[Callable] = None):
        self.cache = cache
        self.key_func = key_func
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if self.key_func:
                cache_key = self.key_func(*args, **kwargs)
            else:
                # 默认：使用函数名和参数哈希
                key_data = (func.__name__, args, tuple(sorted(kwargs.items())))
                key_str = str(key_data)
                cache_key = hashlib.md5(key_str.encode()).hexdigest()
            
            # 尝试从缓存获取
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            self.cache.set(cache_key, result)
            return result
        
        return wrapper

class DiskCache:
    """磁盘缓存"""
    
    def __init__(self, cache_dir: str, max_size_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 元数据存储
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        if self.metadata_file.exists():
            try:
                import json
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            import json
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def get(self, key: str) -> Any:
        """获取缓存值"""
        cache_file = self.cache_dir / f"{key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            # 检查是否过期
            metadata_key = str(cache_file)
            if metadata_key in self.metadata:
                entry_meta = self.metadata[metadata_key]
                if entry_meta.get('expires_at') and time.time() > entry_meta['expires_at']:
                    self.delete(key)
                    return None
            
            # 加载缓存数据
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # 更新访问时间
            self.metadata[metadata_key] = {
                **self.metadata.get(metadata_key, {}),
                'last_access': time.time(),
                'access_count': self.metadata.get(metadata_key, {}).get('access_count', 0) + 1
            }
            self._save_metadata()
            
            return data
        
        except Exception as e:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """设置缓存值"""
        cache_file = self.cache_dir / f"{key}.pkl"
        
        try:
            # 保存数据
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            
            # 更新元数据
            metadata_key = str(cache_file)
            self.metadata[metadata_key] = {
                'created_at': time.time(),
                'last_access': time.time(),
                'access_count': 1,
                'size_bytes': cache_file.stat().st_size if cache_file.exists() else 0,
                'expires_at': time.time() + ttl if ttl else None
            }
            self._save_metadata()
            
            # 清理过期缓存
            self.cleanup_expired()
            
            # 如果超过大小限制，清理最旧的
            self.cleanup_by_size()
        
        except Exception as e:
            pass
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        cache_file = self.cache_dir / f"{key}.pkl"
        
        try:
            if cache_file.exists():
                cache_file.unlink()
            
            # 移除元数据
            metadata_key = str(cache_file)
            if metadata_key in self.metadata:
                del self.metadata[metadata_key]
                self._save_metadata()
            
            return True
        
        except Exception:
            return False
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_count = 0
        current_time = time.time()
        
        for metadata_key, meta in list(self.metadata.items()):
            expires_at = meta.get('expires_at')
            if expires_at and current_time > expires_at:
                cache_file = Path(metadata_key)
                if cache_file.exists():
                    cache_file.unlink()
                del self.metadata[metadata_key]
                expired_count += 1
        
        if expired_count > 0:
            self._save_metadata()
        
        return expired_count
    
    def cleanup_by_size(self) -> int:
        """基于大小清理"""
        if not self.metadata:
            return 0
        
        # 计算总大小
        total_size = sum(meta.get('size_bytes', 0) for meta in self.metadata.values())
        
        if total_size <= self.max_size_bytes:
            return 0
        
        # 按最后访问时间排序，删除最旧的
        sorted_items = sorted(
            self.metadata.items(),
            key=lambda x: x[1].get('last_access', 0)
        )
        
        removed_count = 0
        for metadata_key, meta in sorted_items:
            if total_size <= self.max_size_bytes:
                break
            
            cache_file = Path(metadata_key)
            if cache_file.exists():
                file_size = meta.get('size_bytes', 0)
                cache_file.unlink()
                total_size -= file_size
                del self.metadata[metadata_key]
                removed_count += 1
        
        if removed_count > 0:
            self._save_metadata()
        
        return removed_count
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total_size = sum(meta.get('size_bytes', 0) for meta in self.metadata.values())
        total_files = len(self.metadata)
        
        # 计算命中率（简化版）
        total_access = sum(meta.get('access_count', 0) for meta in self.metadata.values())
        
        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "max_size_mb": self.max_size_bytes / (1024 * 1024),
            "avg_access_count": total_access / total_files if total_files > 0 else 0,
            "cache_dir": str(self.cache_dir)
        }

# 全局缓存实例
memory_cache = LRUCache(max_size=1000, ttl=3600)  # 1小时TTL
disk_cache = DiskCache(cache_dir="./cache", max_size_mb=100)

def cached_function(key_func: Optional[Callable] = None):
    """缓存函数结果的装饰器"""
    return FunctionCache(memory_cache, key_func)