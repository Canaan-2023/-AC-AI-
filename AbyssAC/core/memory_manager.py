"""
Y-Layer Memory Manager
Y层记忆库管理器 - 负责记忆的创建、读取、更新、删除和分类
"""

import os
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config.system_config import get_config


@dataclass
class MemoryEntry:
    """记忆条目数据结构"""
    memory_id: str
    memory_type: str  # 元认知记忆/高阶整合记忆/分类记忆/工作记忆
    value_level: str  # 高价值/中价值/低价值（仅分类记忆）
    timestamp: str
    confidence: float
    user_input: str
    ai_response: str
    extra_analysis: str = ""
    
    def to_text(self) -> str:
        """转换为文本格式"""
        text = f"""【记忆层级】：{self.memory_type}
【记忆ID】：{self.memory_id}
【记忆时间】：{self.timestamp}
【置信度】：{self.confidence}
【核心内容】：
用户输入：{self.user_input}
AI响应：{self.ai_response}"""
        if self.extra_analysis:
            text += f"\n{self.extra_analysis}"
        return text
    
    @classmethod
    def from_text(cls, text: str) -> 'MemoryEntry':
        """从文本解析"""
        patterns = {
            'memory_type': r'【记忆层级】：(.+)',
            'memory_id': r'【记忆ID】：(.+)',
            'timestamp': r'【记忆时间】：(.+)',
            'confidence': r'【置信度】：([\d.]+)',
            'user_input': r'用户输入：(.+)',
            'ai_response': r'AI响应：([\s\S]+?)(?=\n【|$)',
        }
        
        data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                if key == 'confidence':
                    value = float(value)
                data[key] = value
        
        return cls(
            memory_id=data.get('memory_id', ''),
            memory_type=data.get('memory_type', '分类记忆'),
            value_level='中价值',
            timestamp=data.get('timestamp', ''),
            confidence=data.get('confidence', 0.5),
            user_input=data.get('user_input', ''),
            ai_response=data.get('ai_response', '')
        )


class MemoryManager:
    """记忆管理器"""
    
    # 记忆类型目录映射
    MEMORY_TYPE_DIRS = {
        "元认知记忆": "元认知记忆",
        "高阶整合记忆": "高阶整合记忆",
        "分类记忆": "分类记忆",
        "工作记忆": "工作记忆"
    }
    
    # 价值层级子目录
    VALUE_LEVEL_DIRS = {
        "高价值": "高价值",
        "中价值": "中价值",
        "低价值": "低价值"
    }
    
    def __init__(self):
        self.config = get_config()
        self.memory_root = self.config.paths.memory_root_path
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有记忆目录存在"""
        year, month, day = self.config.time.get_current_date_path()
        
        for mem_type, dir_name in self.MEMORY_TYPE_DIRS.items():
            base_path = os.path.join(self.memory_root, dir_name)
            
            if mem_type == "分类记忆":
                for value_level in self.VALUE_LEVEL_DIRS.values():
                    path = os.path.join(base_path, value_level, year, month, day)
                    os.makedirs(path, exist_ok=True)
            else:
                path = os.path.join(base_path, year, month, day)
                os.makedirs(path, exist_ok=True)
    
    def _get_memory_path(self, memory_id: str, memory_type: str, 
                         value_level: str = "中价值",
                         year: str = None, month: str = None, day: str = None) -> str:
        """获取记忆文件路径"""
        if year is None:
            year, month, day = self.config.time.get_current_date_path()
        
        type_dir = self.MEMORY_TYPE_DIRS.get(memory_type, "分类记忆")
        base_path = os.path.join(self.memory_root, type_dir)
        
        if memory_type == "分类记忆":
            level_dir = self.VALUE_LEVEL_DIRS.get(value_level, "中价值")
            return os.path.join(base_path, level_dir, year, month, day, f"{memory_id}.txt")
        else:
            return os.path.join(base_path, year, month, day, f"{memory_id}.txt")
    
    def _parse_memory_path(self, path: str) -> Dict[str, str]:
        """从路径解析记忆信息"""
        parts = path.replace(self.memory_root, "").split(os.sep)
        info = {
            'memory_type': parts[0] if len(parts) > 0 else '分类记忆',
            'value_level': '中价值',
            'year': parts[-4] if len(parts) > 3 else '',
            'month': parts[-3] if len(parts) > 3 else '',
            'day': parts[-2] if len(parts) > 3 else '',
            'memory_id': parts[-1].replace('.txt', '') if len(parts) > 0 else ''
        }
        
        # 检测价值层级
        if '高价值' in parts:
            info['value_level'] = '高价值'
        elif '中价值' in parts:
            info['value_level'] = '中价值'
        elif '低价值' in parts:
            info['value_level'] = '低价值'
        
        return info
    
    def create_memory(self, user_input: str, ai_response: str,
                     memory_type: str = "分类记忆",
                     value_level: str = "中价值",
                     confidence: float = 0.5,
                     extra_analysis: str = "") -> Optional[str]:
        """创建新记忆"""
        try:
            # 获取唯一记忆ID
            memory_id = str(self.config.counters.get_next_memory_id())
            
            # 创建记忆条目
            memory = MemoryEntry(
                memory_id=memory_id,
                memory_type=memory_type,
                value_level=value_level,
                timestamp=self.config.time.get_current_timestamp(),
                confidence=confidence,
                user_input=user_input,
                ai_response=ai_response,
                extra_analysis=extra_analysis
            )
            
            # 确保目录存在
            year, month, day = self.config.time.get_current_date_path()
            memory_path = self._get_memory_path(memory_id, memory_type, value_level, year, month, day)
            os.makedirs(os.path.dirname(memory_path), exist_ok=True)
            
            # 保存记忆
            with open(memory_path, 'w', encoding='utf-8') as f:
                f.write(memory.to_text())
            
            return memory_id
        except Exception as e:
            print(f"创建记忆失败: {e}")
            return None
    
    def read_memory(self, memory_id: str, memory_type: str = None,
                   value_level: str = None) -> Optional[MemoryEntry]:
        """读取记忆"""
        try:
            # 如果提供了完整信息，直接读取
            if memory_type:
                memory_path = self._get_memory_path(memory_id, memory_type, value_level or "中价值")
                if os.path.exists(memory_path):
                    with open(memory_path, 'r', encoding='utf-8') as f:
                        return MemoryEntry.from_text(f.read())
            
            # 否则搜索所有目录
            for root, dirs, files in os.walk(self.memory_root):
                for file in files:
                    if file == f"{memory_id}.txt":
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            return MemoryEntry.from_text(f.read())
            
            return None
        except Exception as e:
            print(f"读取记忆失败: {e}")
            return None
    
    def read_memory_by_path(self, path: str) -> Optional[str]:
        """通过路径读取记忆原始内容"""
        try:
            # 处理相对路径
            if path.startswith("Y层记忆库/"):
                full_path = path
            else:
                full_path = os.path.join(self.memory_root, path.replace("Y层记忆库/", ""))
            
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return None
        except Exception as e:
            print(f"读取记忆失败: {e}")
            return None
    
    def update_memory(self, memory_id: str, **kwargs) -> bool:
        """更新记忆"""
        try:
            memory = self.read_memory(memory_id)
            if not memory:
                return False
            
            for key, value in kwargs.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            
            # 重新保存
            memory_path = self._find_memory_path(memory_id)
            if memory_path:
                with open(memory_path, 'w', encoding='utf-8') as f:
                    f.write(memory.to_text())
                return True
            return False
        except Exception as e:
            print(f"更新记忆失败: {e}")
            return False
    
    def _find_memory_path(self, memory_id: str) -> Optional[str]:
        """查找记忆文件路径"""
        for root, dirs, files in os.walk(self.memory_root):
            for file in files:
                if file == f"{memory_id}.txt":
                    return os.path.join(root, file)
        return None
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        try:
            memory_path = self._find_memory_path(memory_id)
            if memory_path and os.path.exists(memory_path):
                os.remove(memory_path)
                return True
            return False
        except Exception as e:
            print(f"删除记忆失败: {e}")
            return False
    
    def list_memories(self, memory_type: str = None, value_level: str = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """列出记忆"""
        memories = []
        
        search_root = self.memory_root
        if memory_type:
            search_root = os.path.join(search_root, self.MEMORY_TYPE_DIRS.get(memory_type, ""))
            if value_level and memory_type == "分类记忆":
                search_root = os.path.join(search_root, self.VALUE_LEVEL_DIRS.get(value_level, ""))
        
        for root, dirs, files in os.walk(search_root):
            for file in files:
                if file.endswith('.txt'):
                    memory_id = file.replace('.txt', '')
                    memory_path = os.path.join(root, file)
                    try:
                        with open(memory_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            memory = MemoryEntry.from_text(content)
                            memories.append({
                                'memory_id': memory_id,
                                'path': memory_path,
                                'type': memory.memory_type,
                                'confidence': memory.confidence,
                                'timestamp': memory.timestamp,
                                'user_input': memory.user_input[:100] + '...' if len(memory.user_input) > 100 else memory.user_input
                            })
                    except:
                        pass
                    
                    if len(memories) >= limit:
                        return memories
        
        return memories
    
    def adjust_confidence(self, memory_id: str, delta: float) -> bool:
        """调整记忆置信度"""
        try:
            memory = self.read_memory(memory_id)
            if memory:
                new_confidence = max(0.0, min(1.0, memory.confidence + delta))
                return self.update_memory(memory_id, confidence=new_confidence)
            return False
        except Exception as e:
            print(f"调整置信度失败: {e}")
            return False
    
    def get_work_memories(self) -> List[MemoryEntry]:
        """获取所有工作记忆"""
        memories = []
        work_path = os.path.join(self.memory_root, "工作记忆")
        
        for root, dirs, files in os.walk(work_path):
            for file in files:
                if file.endswith('.txt'):
                    try:
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            memories.append(MemoryEntry.from_text(f.read()))
                    except:
                        pass
        
        return memories
    
    def clear_work_memories(self) -> bool:
        """清空工作记忆"""
        try:
            work_path = os.path.join(self.memory_root, "工作记忆")
            for root, dirs, files in os.walk(work_path):
                for file in files:
                    if file.endswith('.txt'):
                        os.remove(os.path.join(root, file))
            return True
        except Exception as e:
            print(f"清空工作记忆失败: {e}")
            return False


# 全局记忆管理器实例
_memory_manager = None


def get_memory_manager() -> MemoryManager:
    """获取全局记忆管理器"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
