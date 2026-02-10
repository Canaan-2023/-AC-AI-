"""AbyssAC Y层记忆管理模块

管理所有记忆数据的CRUD操作，包括记忆创建、读取、更新、删除，
以及记忆与NNG的关联管理。
"""

import json
import os
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from utils.file_ops import (
    safe_read_json, safe_write_json, safe_read_text, safe_write_text,
    ensure_date_directory, atomic_counter_increment, FileLock
)
from utils.logger import get_logger


logger = get_logger()


class MemoryType(Enum):
    """记忆类型枚举"""
    META_COGNITIVE = "元认知记忆"
    HIGH_LEVEL = "高阶整合记忆"
    CLASSIFIED = "分类记忆"
    WORKING = "工作记忆"


class ValueLevel(Enum):
    """分类记忆价值层级"""
    HIGH = "高价值"
    MEDIUM = "中价值"
    LOW = "低价值"


@dataclass
class MemoryMetadata:
    """记忆元数据"""
    memory_id: int
    memory_type: str
    value_level: Optional[str]
    confidence: int
    created_at: str
    file_path: str
    associated_nngs: List[str]
    is_deleted: bool = False


class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, base_path: str):
        """
        初始化记忆管理器
        
        Args:
            base_path: 存储基础路径
        """
        self.base_path = base_path
        self.y_layer_path = os.path.join(base_path, "Y层记忆库")
        self.system_path = os.path.join(base_path, "system")
        
        self.counter_file = os.path.join(self.system_path, "memory_counter.txt")
        self.metadata_file = os.path.join(self.system_path, "memory_metadata.json")
        
        # 内存中的元数据缓存
        self._metadata_cache: Dict[int, MemoryMetadata] = {}
        self._cache_loaded = False
        
        self._ensure_structure()
    
    def _ensure_structure(self) -> None:
        """确保目录结构存在"""
        dirs = [
            os.path.join(self.y_layer_path, "元认知记忆"),
            os.path.join(self.y_layer_path, "高阶整合记忆"),
            os.path.join(self.y_layer_path, "分类记忆", "高价值"),
            os.path.join(self.y_layer_path, "分类记忆", "中价值"),
            os.path.join(self.y_layer_path, "分类记忆", "低价值"),
            os.path.join(self.y_layer_path, "工作记忆"),
            self.system_path,
        ]
        
        for d in dirs:
            os.makedirs(d, exist_ok=True)
        
        # 确保计数器文件存在
        if not os.path.exists(self.counter_file):
            with open(self.counter_file, 'w', encoding='utf-8') as f:
                f.write("0")
        
        # 确保元数据文件存在
        if not os.path.exists(self.metadata_file):
            safe_write_json(self.metadata_file, {})
    
    def _load_metadata_cache(self) -> None:
        """加载元数据到内存缓存"""
        if self._cache_loaded:
            return
        
        data = safe_read_json(self.metadata_file, {})
        for mem_id_str, meta in data.items():
            mem_id = int(mem_id_str)
            self._metadata_cache[mem_id] = MemoryMetadata(
                memory_id=mem_id,
                memory_type=meta.get("memory_type", ""),
                value_level=meta.get("value_level"),
                confidence=meta.get("confidence", 70),
                created_at=meta.get("created_at", ""),
                file_path=meta.get("file_path", ""),
                associated_nngs=meta.get("associated_nngs", []),
                is_deleted=meta.get("is_deleted", False)
            )
        
        self._cache_loaded = True
    
    def _save_metadata_cache(self) -> None:
        """保存元数据缓存到文件"""
        data = {}
        for mem_id, meta in self._metadata_cache.items():
            data[str(mem_id)] = {
                "memory_type": meta.memory_type,
                "value_level": meta.value_level,
                "confidence": meta.confidence,
                "created_at": meta.created_at,
                "file_path": meta.file_path,
                "associated_nngs": meta.associated_nngs,
                "is_deleted": meta.is_deleted
            }
        
        safe_write_json(self.metadata_file, data)
    
    def get_next_memory_id(self) -> int:
        """获取下一个记忆ID"""
        return atomic_counter_increment(self.counter_file)
    
    def create_memory(
        self,
        memory_type: MemoryType,
        user_input: str,
        ai_response: str,
        confidence: int = 70,
        value_level: Optional[ValueLevel] = None,
        associated_nngs: Optional[List[str]] = None,
        extra_content: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> int:
        """
        创建新记忆
        
        Args:
            memory_type: 记忆类型
            user_input: 用户输入内容
            ai_response: AI响应内容
            confidence: 置信度 (1-100)
            value_level: 价值层级（仅分类记忆需要）
            associated_nngs: 关联的NNG节点列表
            extra_content: 额外内容（高阶整合和元认知记忆可用）
            timestamp: 时间戳，默认为当前时间
        
        Returns:
            创建的记忆ID
        """
        self._load_metadata_cache()
        
        # 获取记忆ID
        memory_id = self.get_next_memory_id()
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # 确定存储路径
        if memory_type == MemoryType.CLASSIFIED:
            if value_level is None:
                value_level = ValueLevel.MEDIUM
            type_path = os.path.join(
                self.y_layer_path,
                memory_type.value,
                value_level.value
            )
        else:
            type_path = os.path.join(self.y_layer_path, memory_type.value)
        
        # 创建日期目录
        date_dir = ensure_date_directory(type_path, timestamp)
        
        # 生成文件名
        filename = f"{memory_id}.txt"
        filepath = os.path.join(date_dir, filename)
        
        # 构建记忆内容
        created_at = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        content_lines = [
            f"【记忆层级】：{memory_type.value}",
            f"【记忆ID】{memory_id}",
            f"【记忆时间】{created_at}",
            f"【置信度】：{confidence}",
            "【核心内容】：",
            f"用户输入：{user_input}",
            f"AI响应：{ai_response}"
        ]
        
        if extra_content:
            content_lines.append(f"额外说明：{extra_content}")
        
        content = '\n'.join(content_lines)
        
        # 写入文件
        safe_write_text(filepath, content)
        
        # 更新元数据
        self._metadata_cache[memory_id] = MemoryMetadata(
            memory_id=memory_id,
            memory_type=memory_type.value,
            value_level=value_level.value if value_level else None,
            confidence=confidence,
            created_at=created_at,
            file_path=filepath,
            associated_nngs=associated_nngs or [],
            is_deleted=False
        )
        
        self._save_metadata_cache()
        
        logger.info(f"创建记忆成功: ID={memory_id}, 类型={memory_type.value}, 路径={filepath}")
        
        return memory_id
    
    def get_memory(self, memory_id: int) -> Optional[str]:
        """
        读取记忆内容
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            记忆内容，不存在则返回None
        """
        self._load_metadata_cache()
        
        meta = self._metadata_cache.get(memory_id)
        if not meta or meta.is_deleted:
            return None
        
        try:
            return safe_read_text(meta.file_path)
        except Exception as e:
            logger.error(f"读取记忆失败 ID={memory_id}: {e}")
            return None
    
    def get_memory_metadata(self, memory_id: int) -> Optional[MemoryMetadata]:
        """
        获取记忆元数据
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            记忆元数据
        """
        self._load_metadata_cache()
        return self._metadata_cache.get(memory_id)
    
    def update_memory(
        self,
        memory_id: int,
        user_input: Optional[str] = None,
        ai_response: Optional[str] = None,
        confidence: Optional[int] = None,
        extra_content: Optional[str] = None
    ) -> bool:
        """
        更新记忆内容
        
        Args:
            memory_id: 记忆ID
            user_input: 新的用户输入
            ai_response: 新的AI响应
            confidence: 新的置信度
            extra_content: 新的额外内容
        
        Returns:
            是否更新成功
        """
        self._load_metadata_cache()
        
        meta = self._metadata_cache.get(memory_id)
        if not meta or meta.is_deleted:
            return False
        
        # 读取原内容
        old_content = self.get_memory(memory_id)
        if not old_content:
            return False
        
        # 解析原内容
        old_user_input = self._extract_field(old_content, "用户输入")
        old_ai_response = self._extract_field(old_content, "AI响应")
        old_extra = self._extract_field(old_content, "额外说明")
        
        # 使用新值或保留旧值
        new_user_input = user_input if user_input is not None else old_user_input
        new_ai_response = ai_response if ai_response is not None else old_ai_response
        new_confidence = confidence if confidence is not None else meta.confidence
        new_extra = extra_content if extra_content is not None else old_extra
        
        # 构建新内容
        content_lines = [
            f"【记忆层级】：{meta.memory_type}",
            f"【记忆ID】{memory_id}",
            f"【记忆时间】{meta.created_at}",
            f"【置信度】：{new_confidence}",
            "【核心内容】：",
            f"用户输入：{new_user_input}",
            f"AI响应：{new_ai_response}"
        ]
        
        if new_extra:
            content_lines.append(f"额外说明：{new_extra}")
        
        content = '\n'.join(content_lines)
        
        # 写入文件
        safe_write_text(meta.file_path, content)
        
        # 更新元数据
        meta.confidence = new_confidence
        self._save_metadata_cache()
        
        logger.info(f"更新记忆成功: ID={memory_id}")
        
        return True
    
    def _extract_field(self, content: str, field_name: str) -> str:
        """从记忆内容中提取字段"""
        pattern = rf"{field_name}：(.*?)($|\n)"
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""
    
    def delete_memory(self, memory_id: int, permanent: bool = False) -> bool:
        """
        删除记忆（标记删除或永久删除）
        
        Args:
            memory_id: 记忆ID
            permanent: 是否永久删除
        
        Returns:
            是否删除成功
        """
        self._load_metadata_cache()
        
        meta = self._metadata_cache.get(memory_id)
        if not meta:
            return False
        
        if permanent:
            # 永久删除文件
            try:
                if os.path.exists(meta.file_path):
                    os.remove(meta.file_path)
            except Exception as e:
                logger.error(f"永久删除记忆文件失败 ID={memory_id}: {e}")
                return False
            
            # 从元数据中移除
            del self._metadata_cache[memory_id]
        else:
            # 标记删除
            meta.is_deleted = True
        
        self._save_metadata_cache()
        
        logger.info(f"删除记忆成功: ID={memory_id}, 永久={permanent}")
        
        return True
    
    def add_nng_association(self, memory_id: int, nng_id: str) -> bool:
        """
        添加NNG关联
        
        Args:
            memory_id: 记忆ID
            nng_id: NGG节点ID
        
        Returns:
            是否添加成功
        """
        self._load_metadata_cache()
        
        meta = self._metadata_cache.get(memory_id)
        if not meta or meta.is_deleted:
            return False
        
        if nng_id not in meta.associated_nngs:
            meta.associated_nngs.append(nng_id)
            self._save_metadata_cache()
            logger.info(f"添加NNG关联: 记忆ID={memory_id}, NNG={nng_id}")
        
        return True
    
    def remove_nng_association(self, memory_id: int, nng_id: str) -> bool:
        """
        移除NNG关联
        
        Args:
            memory_id: 记忆ID
            nng_id: NGG节点ID
        
        Returns:
            是否移除成功
        """
        self._load_metadata_cache()
        
        meta = self._metadata_cache.get(memory_id)
        if not meta or meta.is_deleted:
            return False
        
        if nng_id in meta.associated_nngs:
            meta.associated_nngs.remove(nng_id)
            self._save_metadata_cache()
            logger.info(f"移除NNG关联: 记忆ID={memory_id}, NNG={nng_id}")
        
        return True
    
    def get_memories_by_nng(self, nng_id: str, include_deleted: bool = False) -> List[int]:
        """
        获取关联到指定NNG的所有记忆
        
        Args:
            nng_id: NGG节点ID
            include_deleted: 是否包含已删除的记忆
        
        Returns:
            记忆ID列表
        """
        self._load_metadata_cache()
        
        result = []
        for mem_id, meta in self._metadata_cache.items():
            if nng_id in meta.associated_nngs:
                if include_deleted or not meta.is_deleted:
                    result.append(mem_id)
        
        return result
    
    def get_working_memory_count(self) -> int:
        """获取工作记忆数量"""
        self._load_metadata_cache()
        
        count = 0
        for meta in self._metadata_cache.values():
            if (meta.memory_type == MemoryType.WORKING.value and 
                not meta.is_deleted):
                count += 1
        
        return count
    
    def get_working_memories(self, limit: Optional[int] = None) -> List[Tuple[int, str]]:
        """
        获取工作记忆列表
        
        Args:
            limit: 限制数量
        
        Returns:
            (记忆ID, 记忆内容)列表，按创建时间排序
        """
        self._load_metadata_cache()
        
        # 筛选工作记忆并按时间排序
        working = []
        for mem_id, meta in self._metadata_cache.items():
            if (meta.memory_type == MemoryType.WORKING.value and 
                not meta.is_deleted):
                working.append((mem_id, meta.created_at))
        
        working.sort(key=lambda x: x[1])
        
        if limit:
            working = working[:limit]
        
        result = []
        for mem_id, _ in working:
            content = self.get_memory(mem_id)
            if content:
                result.append((mem_id, content))
        
        return result
    
    def clear_working_memory(self) -> int:
        """
        清空工作记忆
        
        Returns:
            删除的记忆数量
        """
        self._load_metadata_cache()
        
        count = 0
        for mem_id, meta in list(self._metadata_cache.items()):
            if (meta.memory_type == MemoryType.WORKING.value and 
                not meta.is_deleted):
                self.delete_memory(mem_id, permanent=True)
                count += 1
        
        logger.info(f"清空工作记忆: 删除{count}条")
        
        return count
    
    def get_memories_by_confidence(
        self,
        min_confidence: int = 0,
        max_confidence: int = 100,
        memory_type: Optional[MemoryType] = None
    ) -> List[int]:
        """
        按置信度范围获取记忆
        
        Args:
            min_confidence: 最小置信度
            max_confidence: 最大置信度
            memory_type: 记忆类型筛选
        
        Returns:
            记忆ID列表
        """
        self._load_metadata_cache()
        
        result = []
        for mem_id, meta in self._metadata_cache.items():
            if meta.is_deleted:
                continue
            
            if min_confidence <= meta.confidence <= max_confidence:
                if memory_type is None or meta.memory_type == memory_type.value:
                    result.append(mem_id)
        
        return result
    
    def update_confidence(self, memory_id: int, delta: int) -> bool:
        """
        更新记忆置信度（增减）
        
        Args:
            memory_id: 记忆ID
            delta: 置信度变化值（可为负）
        
        Returns:
            是否更新成功
        """
        self._load_metadata_cache()
        
        meta = self._metadata_cache.get(memory_id)
        if not meta or meta.is_deleted:
            return False
        
        new_confidence = max(0, min(100, meta.confidence + delta))
        meta.confidence = new_confidence
        self._save_metadata_cache()
        
        # 同时更新文件内容
        self.update_memory(memory_id, confidence=new_confidence)
        
        logger.info(f"更新置信度: 记忆ID={memory_id}, 新值={new_confidence}")
        
        return True
    
    def build_memory_index(self) -> Dict[int, MemoryMetadata]:
        """
        构建内存索引（扫描所有记忆文件）
        
        Returns:
            记忆ID到元数据的映射
        """
        self._metadata_cache.clear()
        
        # 扫描所有记忆文件
        for root, dirs, files in os.walk(self.y_layer_path):
            for filename in files:
                if filename.endswith('.txt'):
                    filepath = os.path.join(root, filename)
                    try:
                        content = safe_read_text(filepath)
                        
                        # 提取记忆ID
                        match = re.search(r'【记忆ID】(\d+)', content)
                        if match:
                            mem_id = int(match.group(1))
                            
                            # 提取其他信息
                            mem_type = self._extract_field(content, "【记忆层级】")
                            confidence_match = re.search(r'【置信度】：(\d+)', content)
                            confidence = int(confidence_match.group(1)) if confidence_match else 70
                            created_at = self._extract_field(content, "【记忆时间】")
                            
                            # 确定价值层级
                            value_level = None
                            if "分类记忆" in mem_type:
                                if "高价值" in root:
                                    value_level = ValueLevel.HIGH.value
                                elif "中价值" in root:
                                    value_level = ValueLevel.MEDIUM.value
                                elif "低价值" in root:
                                    value_level = ValueLevel.LOW.value
                            
                            self._metadata_cache[mem_id] = MemoryMetadata(
                                memory_id=mem_id,
                                memory_type=mem_type,
                                value_level=value_level,
                                confidence=confidence,
                                created_at=created_at,
                                file_path=filepath,
                                associated_nngs=[],
                                is_deleted=False
                            )
                    
                    except Exception as e:
                        logger.warning(f"扫描记忆文件失败 {filepath}: {e}")
        
        # 加载已有的关联信息
        existing = safe_read_json(self.metadata_file, {})
        for mem_id_str, meta in existing.items():
            mem_id = int(mem_id_str)
            if mem_id in self._metadata_cache:
                self._metadata_cache[mem_id].associated_nngs = meta.get("associated_nngs", [])
                self._metadata_cache[mem_id].is_deleted = meta.get("is_deleted", False)
        
        self._save_metadata_cache()
        self._cache_loaded = True
        
        logger.info(f"构建记忆索引完成: 共{len(self._metadata_cache)}条记忆")
        
        return self._metadata_cache
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Returns:
            统计信息字典
        """
        self._load_metadata_cache()
        
        stats = {
            "total": 0,
            "by_type": {},
            "by_value_level": {},
            "deleted": 0,
            "avg_confidence": 0,
            "working_memory": 0
        }
        
        total_confidence = 0
        
        for meta in self._metadata_cache.values():
            if meta.is_deleted:
                stats["deleted"] += 1
                continue
            
            stats["total"] += 1
            total_confidence += meta.confidence
            
            # 按类型统计
            mem_type = meta.memory_type
            stats["by_type"][mem_type] = stats["by_type"].get(mem_type, 0) + 1
            
            # 按价值层级统计
            if meta.value_level:
                stats["by_value_level"][meta.value_level] = \
                    stats["by_value_level"].get(meta.value_level, 0) + 1
            
            # 工作记忆
            if mem_type == MemoryType.WORKING.value:
                stats["working_memory"] += 1
        
        if stats["total"] > 0:
            stats["avg_confidence"] = round(total_confidence / stats["total"], 2)
        
        return stats
