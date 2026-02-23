"""并行IO管理器模块"""

import os
import concurrent.futures
from typing import Dict, List, Optional, Any

class ParallelIOManager:
    """并行IO管理器类"""
    
    def __init__(self, max_workers: int = 4):
        """初始化并行IO管理器
        
        Args:
            max_workers: 最大工作线程数
        """
        self.max_workers = max_workers
    
    def read_files(self, paths: List[str], base_dir: str = '') -> Dict[str, Any]:
        """并行读取多个文件
        
        Args:
            paths: 文件路径列表
            base_dir: 基础目录路径
            
        Returns:
            包含文件路径和内容的字典
        """
        results = {}
        
        # 使用ThreadPoolExecutor并行读取文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有读取任务
            future_to_path = {
                executor.submit(self._read_file, os.path.join(base_dir, path)):
                path for path in paths
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    content = future.result()
                    results[path] = content
                except Exception as e:
                    results[path] = {'error': str(e)}
        
        return results
    
    def _read_file(self, file_path: str) -> Any:
        """读取单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 检查文件是否是普通文件
            if not os.path.isfile(file_path):
                raise IsADirectoryError(f"路径不是文件: {file_path}")
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                raise ValueError(f"文件过大: {file_path}, 大小: {file_size} 字节")
            
            # 根据文件扩展名选择读取方式
            if file_path.endswith('.json'):
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.endswith('.md'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # 对于其他文件类型，返回文件元数据
                import mimetypes
                mime_type, _ = mimetypes.guess_type(file_path)
                return {
                    'file_path': file_path,
                    'file_size': file_size,
                    'mime_type': mime_type or 'application/octet-stream',
                    'is_binary': True
                }
        except Exception as e:
            raise e
    
    def write_files(self, file_contents: Dict[str, Any], base_dir: str = '') -> Dict[str, bool]:
        """并行写入多个文件
        
        Args:
            file_contents: 包含文件路径和内容的字典
            base_dir: 基础目录路径
            
        Returns:
            包含文件路径和写入结果的字典
        """
        results = {}
        
        # 使用ThreadPoolExecutor并行写入文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有写入任务
            future_to_path = {}
            for path, content in file_contents.items():
                full_path = os.path.join(base_dir, path)
                future_to_path[executor.submit(self._write_file, full_path, content)] = path
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    future.result()
                    results[path] = True
                except Exception as e:
                    results[path] = False
        
        return results
    
    def _write_file(self, file_path: str, content: Any) -> None:
        """写入单个文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
        """
        try:
            # 确保目录存在
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # 根据内容类型选择写入方式
            if isinstance(content, dict):
                # JSON格式
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
            elif isinstance(content, str):
                # 文本格式
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                # 其他格式
                raise TypeError(f"不支持的内容类型: {type(content)}")
        except Exception as e:
            raise e
    
    def exists(self, paths: List[str], base_dir: str = '') -> Dict[str, bool]:
        """并行检查多个文件是否存在
        
        Args:
            paths: 文件路径列表
            base_dir: 基础目录路径
            
        Returns:
            包含文件路径和存在状态的字典
        """
        results = {}
        
        # 使用ThreadPoolExecutor并行检查
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有检查任务
            future_to_path = {
                executor.submit(os.path.exists, os.path.join(base_dir, path)):
                path for path in paths
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    exists = future.result()
                    results[path] = exists
                except Exception:
                    results[path] = False
        
        return results
    
    def get_file_info(self, paths: List[str], base_dir: str = '') -> Dict[str, Dict[str, Any]]:
        """并行获取多个文件的信息
        
        Args:
            paths: 文件路径列表
            base_dir: 基础目录路径
            
        Returns:
            包含文件路径和信息的字典
        """
        results = {}
        
        # 使用ThreadPoolExecutor并行获取文件信息
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有获取信息任务
            future_to_path = {
                executor.submit(self._get_file_info, os.path.join(base_dir, path)):
                path for path in paths
            }
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    info = future.result()
                    results[path] = info
                except Exception as e:
                    results[path] = {'error': str(e)}
        
        return results
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """获取单个文件的信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 获取文件信息
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            
            return {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'mime_type': mime_type or 'application/octet-stream',
                'is_file': os.path.isfile(file_path),
                'is_dir': os.path.isdir(file_path),
                'mod_time': os.path.getmtime(file_path)
            }
        except Exception as e:
            raise e