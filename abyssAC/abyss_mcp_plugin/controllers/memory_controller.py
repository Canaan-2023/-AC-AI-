#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆控制器 - 记忆相关操作
"""

from typing import Dict, Any, List, Optional
from ..models.memory_system import MemorySystem, MemoryLayer
from ..core.logger import AbyssLogger


class MemoryController:
    """记忆控制器"""
    
    def __init__(self, memory_system: MemorySystem):
        self.memory_system = memory_system
        self.logger = AbyssLogger("MemoryController")
    
    def create_memory(self, content: str, layer: str = "CATEGORICAL", 
                     category: str = "未分类", metadata: Dict[str, Any] = None) -> str:
        """创建记忆"""
        layer_enum = getattr(MemoryLayer, layer, MemoryLayer.CATEGORICAL)
        memory_id = self.memory_system.create_memory(
            content, layer=layer_enum, category=category, metadata=metadata
        )
        self.logger.info(f"创建记忆: {memory_id}")
        return memory_id
    
    def get_memories(self, layer: Optional[str] = None, 
                    category: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取记忆列表"""
        layer_enum = None
        if layer:
            layer_enum = getattr(MemoryLayer, layer, None)
        
        memories = self.memory_system.retrieve_memory(
            query="", layer=layer_enum, category=category, limit=limit
        )
        
        return [
            {
                'id': mem.id,
                'content': mem.content,
                'layer': mem.layer.name,
                'category': mem.category,
                'timestamp': mem.timestamp,
                'importance_score': mem.importance_score,
                'activation_count': mem.activation_count,
                'keywords': mem.keywords
            }
            for mem in memories
        ]
    
    def search_memories(self, query: str, layer: Optional[str] = None,
                       category: Optional[str] = None, limit: int = 10,
                       advanced: bool = False) -> List[Dict[str, Any]]:
        """搜索记忆"""
        layer_enum = None
        if layer:
            layer_enum = getattr(MemoryLayer, layer, None)
        
        if advanced:
            memories = self.memory_system.advanced_retrieve(
                query, layer=layer_enum, limit=limit
            )
        else:
            memories = self.memory_system.retrieve_memory(
                query=query, layer=layer_enum, category=category, limit=limit
            )
        
        return [
            {
                'id': mem.id,
                'content': mem.content,
                'layer': mem.layer.name,
                'category': mem.category,
                'timestamp': mem.timestamp,
                'importance_score': mem.importance_score,
                'activation_count': mem.activation_count,
                'keywords': mem.keywords
            }
            for mem in memories
        ]
    
    def fuse_memories(self, category: str) -> List[str]:
        """融合记忆"""
        fused_ids = self.memory_system.fuse_related_memories(category)
        self.logger.info(f"融合记忆: {len(fused_ids)} 个")
        return fused_ids
    
    def discover_patterns(self) -> List[Dict[str, Any]]:
        """发现记忆模式"""
        return self.memory_system.discover_patterns()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        return self.memory_system.get_stats()