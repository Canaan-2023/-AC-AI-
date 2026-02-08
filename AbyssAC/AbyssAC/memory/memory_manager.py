"""
Y层记忆库管理模块
负责记忆的存储、读取、索引管理
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class MemoryType(Enum):
    """记忆类型"""
    META_COGNITION = "元认知记忆"
    HIGH_LEVEL = "高阶整合记忆"
    CLASSIFIED = "分类记忆"
    WORKING = "工作记忆"


class ValueLevel(Enum):
    """价值层级（仅用于分类记忆）"""
    HIGH = "高价值"
    MEDIUM = "中价值"
    LOW = "低价值"


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: int
    content: str
    memory_type: MemoryType
    value_level: Optional[ValueLevel] = None
    timestamp: str = ""
    file_path: str = ""
    nng_nodes: List[str] = None  # 关联的NNG节点列表
    
    def __post_init__(self):
        if self.timestamp == "":
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.nng_nodes is None:
            self.nng_nodes = []


class MemoryManager:
    """记忆库管理器"""
    
    def __init__(self, base_path: str = "Y层记忆库", id_counter_file: str = "id_counter.txt"):
        self.base_path = Path(base_path)
        self.id_counter_file = self.base_path / id_counter_file
        self.lock = threading.Lock()
        
        # 记忆类型目录
        self.dirs = {
            MemoryType.META_COGNITION: self.base_path / "元认知记忆",
            MemoryType.HIGH_LEVEL: self.base_path / "高阶整合记忆",
            MemoryType.CLASSIFIED: self.base_path / "分类记忆",
            MemoryType.WORKING: self.base_path / "工作记忆"
        }
        
        # 价值子目录（仅分类记忆）
        self.value_dirs = {
            ValueLevel.HIGH: self.dirs[MemoryType.CLASSIFIED] / "高价值",
            ValueLevel.MEDIUM: self.dirs[MemoryType.CLASSIFIED] / "中价值",
            ValueLevel.LOW: self.dirs[MemoryType.CLASSIFIED] / "低价值"
        }
        
        # 初始化目录结构
        self._init_directories()
        
    def _init_directories(self):
        """初始化目录结构"""
        # 创建基础目录
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 创建ID计数器文件（如果不存在）
        if not self.id_counter_file.exists():
            with open(self.id_counter_file, 'w', encoding='utf-8') as f:
                f.write("last_id: 0")
        
        # 创建记忆类型目录
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 创建价值子目录
        for dir_path in self.value_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
    def _get_next_id(self) -> int:
        """获取下一个记忆ID（线程安全）"""
        with self.lock:
            try:
                with open(self.id_counter_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    match = re.search(r'last_id:\s*(\d+)', content)
                    current_id = int(match.group(1)) if match else 0
            except:
                current_id = 0
            
            next_id = current_id + 1
            
            with open(self.id_counter_file, 'w', encoding='utf-8') as f:
                f.write(f"last_id: {next_id}")
            
            return next_id
    
    def _get_time_based_path(self, base_dir: Path) -> Path:
        """获取基于时间的目录路径 YYYY/MM/DD"""
        now = datetime.now()
        time_path = base_dir / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"
        time_path.mkdir(parents=True, exist_ok=True)
        return time_path
    
    def _get_target_dir(self, memory_type: MemoryType, value_level: Optional[ValueLevel] = None) -> Path:
        """获取目标目录"""
        if memory_type == MemoryType.CLASSIFIED and value_level:
            return self.value_dirs[value_level]
        return self.dirs[memory_type]
    
    def save_memory(self, content: str, memory_type: MemoryType, 
                    value_level: Optional[ValueLevel] = None,
                    nng_nodes: Optional[List[str]] = None) -> MemoryEntry:
        """
        保存记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            value_level: 价值层级（仅分类记忆需要）
            nng_nodes: 关联的NNG节点列表
            
        Returns:
            MemoryEntry: 保存的记忆条目
        """
        # 获取新ID
        memory_id = self._get_next_id()
        
        # 确定目标目录
        target_base = self._get_target_dir(memory_type, value_level)
        target_dir = self._get_time_based_path(target_base)
        
        # 构建文件路径
        file_path = target_dir / f"{memory_id}.txt"
        
        # 创建记忆条目
        entry = MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            value_level=value_level,
            file_path=str(file_path),
            nng_nodes=nng_nodes or []
        )
        
        # 保存到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[Memory] 已保存记忆 #{memory_id} 到 {file_path}")
        return entry
    
    def get_memory(self, memory_id: int) -> Optional[MemoryEntry]:
        """根据ID获取记忆"""
        # 搜索所有记忆目录
        for memory_type, base_dir in self.dirs.items():
            if memory_type == MemoryType.CLASSIFIED:
                # 分类记忆需要搜索三个价值子目录
                for value_level, value_dir in self.value_dirs.items():
                    entry = self._find_memory_in_dir(memory_id, value_dir, memory_type, value_level)
                    if entry:
                        return entry
            else:
                entry = self._find_memory_in_dir(memory_id, base_dir, memory_type)
                if entry:
                    return entry
        
        return None
    
    def _find_memory_in_dir(self, memory_id: int, base_dir: Path, 
                            memory_type: MemoryType,
                            value_level: Optional[ValueLevel] = None) -> Optional[MemoryEntry]:
        """在指定目录中查找记忆"""
        for file_path in base_dir.rglob(f"{memory_id}.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 获取文件修改时间作为时间戳
                timestamp = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                return MemoryEntry(
                    id=memory_id,
                    content=content,
                    memory_type=memory_type,
                    value_level=value_level,
                    timestamp=timestamp,
                    file_path=str(file_path)
                )
            except Exception as e:
                print(f"[Memory] 读取记忆文件失败 {file_path}: {e}")
        
        return None
    
    def get_working_memories(self, limit: int = 20) -> List[MemoryEntry]:
        """获取最近的工作记忆"""
        memories = []
        working_dir = self.dirs[MemoryType.WORKING]
        
        # 收集所有工作记忆文件
        for file_path in working_dir.rglob("*.txt"):
            try:
                match = re.search(r'(\d+)\.txt$', file_path.name)
                if match:
                    memory_id = int(match.group(1))
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    timestamp = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    
                    memories.append(MemoryEntry(
                        id=memory_id,
                        content=content,
                        memory_type=MemoryType.WORKING,
                        timestamp=timestamp,
                        file_path=str(file_path)
                    ))
            except Exception as e:
                print(f"[Memory] 读取工作记忆失败 {file_path}: {e}")
        
        # 按时间戳排序（最新的在前）
        memories.sort(key=lambda x: x.timestamp, reverse=True)
        return memories[:limit]
    
    def count_working_memories(self) -> int:
        """统计工作记忆数量"""
        count = 0
        working_dir = self.dirs[MemoryType.WORKING]
        for file_path in working_dir.rglob("*.txt"):
            if re.search(r'\d+\.txt$', file_path.name):
                count += 1
        return count
    
    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆"""
        entry = self.get_memory(memory_id)
        if entry and entry.file_path:
            try:
                Path(entry.file_path).unlink()
                print(f"[Memory] 已删除记忆 #{memory_id}")
                return True
            except Exception as e:
                print(f"[Memory] 删除记忆失败 #{memory_id}: {e}")
        return False
    
    def update_memory(self, memory_id: int, new_content: str) -> bool:
        """更新记忆内容"""
        entry = self.get_memory(memory_id)
        if entry and entry.file_path:
            try:
                with open(entry.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[Memory] 已更新记忆 #{memory_id}")
                return True
            except Exception as e:
                print(f"[Memory] 更新记忆失败 #{memory_id}: {e}")
        return False
    
    def get_memories_by_nng_node(self, node_id: str, limit: int = 10) -> List[MemoryEntry]:
        """获取关联到指定NNG节点的记忆"""
        # 注意：这里简化实现，实际应该通过NNG索引
        # 目前返回空列表，由NNGManager维护关联关系
        return []
    
    def get_all_memory_ids(self) -> List[int]:
        """获取所有记忆ID"""
        ids = []
        for memory_type, base_dir in self.dirs.items():
            if memory_type == MemoryType.CLASSIFIED:
                for value_dir in self.value_dirs.values():
                    for file_path in value_dir.rglob("*.txt"):
                        match = re.search(r'(\d+)\.txt$', file_path.name)
                        if match:
                            ids.append(int(match.group(1)))
            else:
                for file_path in base_dir.rglob("*.txt"):
                    match = re.search(r'(\d+)\.txt$', file_path.name)
                    if match:
                        ids.append(int(match.group(1)))
        return sorted(ids)


if __name__ == "__main__":
    # 自测
    print("=" * 60)
    print("MemoryManager模块自测")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    # 创建临时测试目录
    test_dir = tempfile.mkdtemp(prefix="abyssac_test_")
    print(f"\n测试目录: {test_dir}")
    
    try:
        # 初始化记忆管理器
        mm = MemoryManager(base_path=test_dir)
        print("[✓] 记忆管理器初始化成功")
        
        # 测试保存工作记忆
        entry1 = mm.save_memory(
            content="用户问：Python的GIL是什么？",
            memory_type=MemoryType.WORKING
        )
        print(f"[✓] 保存工作记忆 #{entry1.id}")
        
        entry2 = mm.save_memory(
            content="用户问：如何优化Python性能？",
            memory_type=MemoryType.WORKING
        )
        print(f"[✓] 保存工作记忆 #{entry2.id}")
        
        # 测试保存分类记忆
        entry3 = mm.save_memory(
            content="GIL（全局解释器锁）是Python解释器中的机制...",
            memory_type=MemoryType.CLASSIFIED,
            value_level=ValueLevel.HIGH,
            nng_nodes=["1.2.3"]
        )
        print(f"[✓] 保存高价值分类记忆 #{entry3.id}")
        
        # 测试获取记忆
        retrieved = mm.get_memory(entry1.id)
        if retrieved and retrieved.content == entry1.content:
            print(f"[✓] 获取记忆 #{entry1.id} 成功")
        else:
            print(f"[✗] 获取记忆 #{entry1.id} 失败")
        
        # 测试获取工作记忆列表
        working_memories = mm.get_working_memories(limit=10)
        print(f"[✓] 获取工作记忆列表: {len(working_memories)}条")
        
        # 测试统计
        count = mm.count_working_memories()
        print(f"[✓] 工作记忆数量: {count}")
        
        # 测试更新记忆
        success = mm.update_memory(entry1.id, "更新后的内容")
        print(f"[✓] 更新记忆: {'成功' if success else '失败'}")
        
        # 测试获取所有ID
        all_ids = mm.get_all_memory_ids()
        print(f"[✓] 所有记忆ID: {all_ids}")
        
        # 测试删除记忆
        success = mm.delete_memory(entry2.id)
        print(f"[✓] 删除记忆: {'成功' if success else '失败'}")
        
        count_after = mm.count_working_memories()
        print(f"[✓] 删除后工作记忆数量: {count_after}")
        
        print("\n" + "=" * 60)
        print("MemoryManager模块自测通过")
        print("=" * 60)
        
    finally:
        # 清理测试目录
        shutil.rmtree(test_dir, ignore_errors=True)
        print(f"\n已清理测试目录")
