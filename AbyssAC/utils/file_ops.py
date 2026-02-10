"""AbyssAC文件操作工具模块

提供安全的文件读写操作，包含原子性保证和错误处理。
"""

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import fcntl


class FileLock:
    """文件锁，用于并发安全"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.lockfile = None
    
    def __enter__(self):
        lock_path = f"{self.filepath}.lock"
        self.lockfile = open(lock_path, 'w')
        fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_EX)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lockfile:
            fcntl.flock(self.lockfile.fileno(), fcntl.LOCK_UN)
            self.lockfile.close()
            try:
                os.remove(f"{self.filepath}.lock")
            except:
                pass


def safe_read_json(filepath: str, default: Any = None) -> Any:
    """安全读取JSON文件
    
    Args:
        filepath: 文件路径
        default: 读取失败时的默认值
    
    Returns:
        解析后的JSON数据或默认值
    """
    try:
        if not os.path.exists(filepath):
            return default
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析错误 {filepath}: {e}")
    except Exception as e:
        raise IOError(f"文件读取错误 {filepath}: {e}")


def safe_write_json(filepath: str, data: Any, atomic: bool = True) -> None:
    """安全写入JSON文件
    
    Args:
        filepath: 文件路径
        data: 要写入的数据
        atomic: 是否使用原子写入
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if atomic:
            # 原子写入：先写入临时文件，再重命名
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(filepath),
                suffix='.tmp'
            )
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                shutil.move(temp_path, filepath)
            except:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    except Exception as e:
        raise IOError(f"文件写入错误 {filepath}: {e}")


def safe_read_text(filepath: str, default: str = "") -> str:
    """安全读取文本文件
    
    Args:
        filepath: 文件路径
        default: 读取失败时的默认值
    
    Returns:
        文件内容或默认值
    """
    try:
        if not os.path.exists(filepath):
            return default
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"文件读取错误 {filepath}: {e}")


def safe_write_text(filepath: str, content: str, atomic: bool = True) -> None:
    """安全写入文本文件
    
    Args:
        filepath: 文件路径
        content: 要写入的内容
        atomic: 是否使用原子写入
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if atomic:
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(filepath),
                suffix='.tmp'
            )
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(content)
                shutil.move(temp_path, filepath)
            except:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
    
    except Exception as e:
        raise IOError(f"文件写入错误 {filepath}: {e}")


def get_memory_path(base_path: str, memory_type: str, timestamp: datetime) -> str:
    """获取记忆文件的存储路径
    
    Args:
        base_path: 基础路径
        memory_type: 记忆类型
        timestamp: 时间戳
    
    Returns:
        完整的文件夹路径
    """
    path_parts = [
        base_path,
        memory_type,
        str(timestamp.year),
        f"{timestamp.month:02d}",
        f"{timestamp.day:02d}"
    ]
    return os.path.join(*path_parts)


def ensure_date_directory(base_path: str, timestamp: datetime = None) -> str:
    """确保日期目录存在
    
    Args:
        base_path: 基础路径
        timestamp: 时间戳，默认为当前时间
    
    Returns:
        创建的目录路径
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    path = os.path.join(
        base_path,
        str(timestamp.year),
        f"{timestamp.month:02d}",
        f"{timestamp.day:02d}"
    )
    os.makedirs(path, exist_ok=True)
    return path


def list_files_recursive(directory: str, pattern: str = "*") -> List[str]:
    """递归列出目录中的所有文件
    
    Args:
        directory: 目录路径
        pattern: 文件匹配模式
    
    Returns:
        文件路径列表
    """
    files = []
    if not os.path.exists(directory):
        return files
    
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if pattern == "*" or filename.endswith(pattern.replace("*", "")):
                files.append(os.path.join(root, filename))
    
    return files


def get_next_filename(directory: str, extension: str = ".txt") -> str:
    """获取下一个可用的文件名（数字序号）
    
    Args:
        directory: 目录路径
        extension: 文件扩展名
    
    Returns:
        下一个可用的文件名（不含路径）
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return f"1{extension}"
    
    existing = [f for f in os.listdir(directory) 
                if f.endswith(extension) and f[:-len(extension)].isdigit()]
    
    if not existing:
        return f"1{extension}"
    
    numbers = [int(f[:-len(extension)]) for f in existing]
    next_num = max(numbers) + 1
    return f"{next_num}{extension}"


def atomic_counter_increment(counter_file: str) -> int:
    """原子性递增计数器
    
    Args:
        counter_file: 计数器文件路径
    
    Returns:
        递增后的值
    """
    with FileLock(counter_file):
        try:
            if os.path.exists(counter_file):
                with open(counter_file, 'r', encoding='utf-8') as f:
                    current = int(f.read().strip() or "0")
            else:
                current = 0
            
            next_val = current + 1
            
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(counter_file) or '.',
                suffix='.tmp'
            )
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    f.write(str(next_val))
                shutil.move(temp_path, counter_file)
            except:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                raise
            
            return next_val
        except Exception as e:
            raise IOError(f"计数器操作失败: {e}")


def backup_file(filepath: str, backup_dir: Optional[str] = None) -> str:
    """备份文件
    
    Args:
        filepath: 要备份的文件路径
        backup_dir: 备份目录，默认为文件所在目录的.backup子目录
    
    Returns:
        备份文件路径
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"文件不存在: {filepath}")
    
    if backup_dir is None:
        backup_dir = os.path.join(os.path.dirname(filepath), '.backup')
    
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.basename(filepath)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}.bak")
    
    shutil.copy2(filepath, backup_path)
    return backup_path
