"""
Y层记忆库管理器
"""
import json
import os
import re
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    META_COGNITION = "元认知"
    HIGH_LEVEL = "高阶整合"
    CLASSIFIED = "分类"
    WORKING = "工作"
    MULTIMEDIA = "多媒体"


class ValueLevel(Enum):
    """价值层级"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class MemoryInfo:
    """记忆信息"""
    memory_id: int
    content: str
    memory_type: str
    value_level: Optional[str] = None
    timestamp: str = ""
    file_path: str = ""
    is_multimedia: bool = False
    file_extension: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MemoryManager:
    """Y层记忆库管理器"""
    
    def __init__(self, config: Dict):
        self.memory_dir = Path(config["paths"]["memory_dir"])
        self.id_counter_file = self.memory_dir / "id_counter.txt"
        
        # 子目录
        self.meta_cognition_dir = self.memory_dir / "元认知记忆"
        self.high_level_dir = self.memory_dir / "高阶整合记忆"
        self.classified_dir = self.memory_dir / "分类记忆"
        self.working_dir = self.memory_dir / "工作记忆"
        
        # 价值层级目录
        self.high_value_dir = self.classified_dir / "高价值"
        self.medium_value_dir = self.classified_dir / "中价值"
        self.low_value_dir = self.classified_dir / "低价值"
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保目录存在"""
        for d in [self.meta_cognition_dir, self.high_level_dir, self.classified_dir,
                  self.working_dir, self.high_value_dir, self.medium_value_dir, 
                  self.low_value_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def _get_next_id(self) -> int:
        """获取下一个记忆ID（线程安全）"""
        with open(self.id_counter_file, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                content = f.read().strip()
                match = re.search(r'last_id:\s*(\d+)', content)
                current_id = int(match.group(1)) if match else 0
                next_id = current_id + 1
                
                f.seek(0)
                f.write(f"last_id: {next_id}\n")
                f.truncate()
                return next_id
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def _get_current_id(self) -> int:
        """获取当前最大ID"""
        try:
            with open(self.id_counter_file, 'r') as f:
                content = f.read().strip()
                match = re.search(r'last_id:\s*(\d+)', content)
                return int(match.group(1)) if match else 0
        except:
            return 0
    
    def _get_time_path(self, base_dir: Path) -> Path:
        """获取基于当前时间的目录路径"""
        now = datetime.now()
        path = base_dir / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def _get_dir_by_type(self, memory_type: MemoryType, value_level: Optional[ValueLevel] = None) -> Path:
        """根据记忆类型获取目录"""
        if memory_type == MemoryType.META_COGNITION:
            return self.meta_cognition_dir
        elif memory_type == MemoryType.HIGH_LEVEL:
            return self.high_level_dir
        elif memory_type == MemoryType.WORKING:
            return self.working_dir
        elif memory_type == MemoryType.CLASSIFIED:
            if value_level == ValueLevel.HIGH:
                return self.high_value_dir
            elif value_level == ValueLevel.MEDIUM:
                return self.medium_value_dir
            elif value_level == ValueLevel.LOW:
                return self.low_value_dir
            else:
                return self.medium_value_dir  # 默认中价值
        else:
            return self.working_dir
    
    def save_memory(self, content: str, memory_type: MemoryType,
                   value_level: Optional[ValueLevel] = None,
                   is_multimedia: bool = False,
                   file_extension: str = ".txt") -> MemoryInfo:
        """
        保存记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            value_level: 价值层级（仅分类记忆需要）
            is_multimedia: 是否为多媒体
            file_extension: 文件扩展名
        
        Returns:
            MemoryInfo对象
        """
        memory_id = self._get_next_id()
        base_dir = self._get_dir_by_type(memory_type, value_level)
        time_dir = self._get_time_path(base_dir)
        
        # 文件名: ID.txt 或 ID.jpg 等
        filename = f"{memory_id}{file_extension}"
        file_path = time_dir / filename
        
        # 保存文件
        if is_multimedia and file_extension != ".txt":
            # 多媒体文件需要特殊处理（假设content是文件内容或路径）
            with open(file_path, 'wb') as f:
                if isinstance(content, bytes):
                    f.write(content)
                else:
                    f.write(content.encode())
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        info = MemoryInfo(
            memory_id=memory_id,
            content=content if not is_multimedia else f"[多媒体文件: {filename}]",
            memory_type=memory_type.value,
            value_level=value_level.value if value_level else None,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_path=str(file_path),
            is_multimedia=is_multimedia,
            file_extension=file_extension
        )
        
        return info
    
    def get_memory(self, memory_id: int) -> Optional[MemoryInfo]:
        """根据ID获取记忆"""
        # 遍历所有目录查找
        search_dirs = [
            self.meta_cognition_dir, self.high_level_dir,
            self.high_value_dir, self.medium_value_dir, self.low_value_dir,
            self.working_dir
        ]
        
        for base_dir in search_dirs:
            for txt_file in base_dir.rglob(f"{memory_id}.txt"):
                return self._load_memory_info(txt_file, memory_id)
            # 也查找多媒体文件
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.wav']:
                for media_file in base_dir.rglob(f"{memory_id}{ext}"):
                    return self._load_memory_info(media_file, memory_id, is_multimedia=True)
        
        return None
    
    def _load_memory_info(self, file_path: Path, memory_id: int, 
                          is_multimedia: bool = False) -> MemoryInfo:
        """从文件路径加载记忆信息"""
        try:
            if is_multimedia:
                content = f"[多媒体文件: {file_path.name}]"
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # 推断记忆类型
            path_str = str(file_path)
            if "元认知记忆" in path_str:
                mem_type = MemoryType.META_COGNITION.value
                value_level = None
            elif "高阶整合记忆" in path_str:
                mem_type = MemoryType.HIGH_LEVEL.value
                value_level = None
            elif "工作记忆" in path_str:
                mem_type = MemoryType.WORKING.value
                value_level = None
            elif "分类记忆" in path_str:
                mem_type = MemoryType.CLASSIFIED.value
                if "高价值" in path_str:
                    value_level = ValueLevel.HIGH.value
                elif "低价值" in path_str:
                    value_level = ValueLevel.LOW.value
                else:
                    value_level = ValueLevel.MEDIUM.value
            else:
                mem_type = MemoryType.WORKING.value
                value_level = None
            
            # 获取文件修改时间
            stat = file_path.stat()
            timestamp = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            return MemoryInfo(
                memory_id=memory_id,
                content=content,
                memory_type=mem_type,
                value_level=value_level,
                timestamp=timestamp,
                file_path=str(file_path),
                is_multimedia=is_multimedia,
                file_extension=file_path.suffix
            )
        except Exception as e:
            return MemoryInfo(
                memory_id=memory_id,
                content=f"[加载失败: {e}]",
                memory_type="未知",
                timestamp="",
                file_path=str(file_path)
            )
    
    def get_working_memories(self, limit: Optional[int] = None) -> List[MemoryInfo]:
        """获取工作记忆列表"""
        memories = []
        for txt_file in self.working_dir.rglob("*.txt"):
            try:
                memory_id = int(txt_file.stem)
                info = self._load_memory_info(txt_file, memory_id)
                memories.append(info)
            except:
                pass
        
        # 按时间排序
        memories.sort(key=lambda x: x.timestamp, reverse=True)
        
        if limit:
            memories = memories[:limit]
        
        return memories
    
    def count_working_memories(self) -> int:
        """统计工作记忆数量"""
        count = 0
        for _ in self.working_dir.rglob("*.txt"):
            count += 1
        return count
    
    def delete_memory(self, memory_id: int) -> bool:
        """删除记忆"""
        info = self.get_memory(memory_id)
        if info and info.file_path:
            try:
                Path(info.file_path).unlink()
                return True
            except:
                pass
        return False
    
    def update_memory(self, memory_id: int, new_content: str) -> bool:
        """更新记忆内容"""
        info = self.get_memory(memory_id)
        if info and info.file_path:
            try:
                with open(info.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True
            except:
                pass
        return False
    
    def search_memories(self, keyword: str, limit: int = 10) -> List[MemoryInfo]:
        """搜索记忆（简单关键词匹配）"""
        results = []
        search_dirs = [
            self.meta_cognition_dir, self.high_level_dir,
            self.high_value_dir, self.medium_value_dir, self.low_value_dir,
            self.working_dir
        ]
        
        for base_dir in search_dirs:
            for txt_file in base_dir.rglob("*.txt"):
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if keyword.lower() in content.lower():
                        memory_id = int(txt_file.stem)
                        info = self._load_memory_info(txt_file, memory_id)
                        results.append(info)
                        if len(results) >= limit:
                            return results
                except:
                    pass
        
        return results
    
    def get_all_memory_summaries(self, limit: int = 100) -> List[Dict]:
        """获取所有记忆摘要（用于NNG关联）"""
        summaries = []
        current_id = self._get_current_id()
        
        for i in range(1, current_id + 1):
            info = self.get_memory(i)
            if info:
                # 生成摘要（取前100字符）
                summary = info.content[:100] + "..." if len(info.content) > 100 else info.content
                summaries.append({
                    "记忆ID": i,
                    "摘要": summary,
                    "记忆类型": info.memory_type,
                    "价值层级": info.value_level,
                    "时间": info.timestamp
                })
        
        return summaries[-limit:]  # 返回最近的


# 全局实例
_memory_manager: Optional[MemoryManager] = None


def init_memory_manager(config: Dict) -> MemoryManager:
    """初始化记忆管理器"""
    global _memory_manager
    _memory_manager = MemoryManager(config)
    return _memory_manager


def get_memory_manager() -> Optional[MemoryManager]:
    """获取记忆管理器实例"""
    return _memory_manager
