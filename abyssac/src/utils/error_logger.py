"""错误记录管理器模块"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime


class ErrorLogger:
    """错误记录管理器类"""
    
    def __init__(self, log_dir: str = 'storage/logs'):
        """初始化错误记录管理器
        
        Args:
            log_dir: 日志目录
        """
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.errors_file = os.path.join(log_dir, 'navigation_errors.json')
        self.errors = self._load_errors()
    
    def _load_errors(self) -> List[Dict[str, Any]]:
        """加载错误记录"""
        try:
            if os.path.exists(self.errors_file):
                with open(self.errors_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    
    def _save_errors(self):
        """保存错误记录"""
        try:
            with open(self.errors_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def log_navigation_error(self, error_type: str, details: Dict[str, Any]):
        """记录导航错误
        
        Args:
            error_type: 错误类型
            details: 错误详情
        """
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'details': details
        }
        
        self.errors.append(error_record)
        
        if len(self.errors) > 1000:
            self.errors = self.errors[-500:]
        
        self._save_errors()
    
    def log_max_depth_reached(self, context: Dict[str, Any]):
        """记录达到最大深度
        
        Args:
            context: 上下文信息
        """
        self.log_navigation_error('max_depth_reached', {
            'user_input': context.get('user_input', ''),
            'current_depth': context.get('current_depth', 0),
            'max_depth': context.get('max_depth', 0),
            'paths_collected': len(context.get('nng_paths', [])),
            'errors': context.get('errors', [])
        })
    
    def log_path_not_found(self, path: str, context: Dict[str, Any]):
        """记录路径不存在
        
        Args:
            path: 不存在的路径
            context: 上下文信息
        """
        self.log_navigation_error('path_not_found', {
            'path': path,
            'user_input': context.get('user_input', ''),
            'visited_paths': list(context.get('visited_paths', set()))
        })
    
    def log_circular_path(self, path: str, context: Dict[str, Any]):
        """记录循环路径
        
        Args:
            path: 循环路径
            context: 上下文信息
        """
        self.log_navigation_error('circular_path', {
            'path': path,
            'user_input': context.get('user_input', '')
        })
    
    def get_errors_for_dmn(self) -> List[Dict[str, Any]]:
        """获取供DMN优化的错误记录
        
        Returns:
            错误记录列表
        """
        return self.errors[-50:]
    
    def get_errors_by_type(self, error_type: str) -> List[Dict[str, Any]]:
        """按类型获取错误记录
        
        Args:
            error_type: 错误类型
            
        Returns:
            错误记录列表
        """
        return [e for e in self.errors if e.get('type') == error_type]
    
    def clear_old_errors(self, days: int = 7):
        """清理旧错误记录
        
        Args:
            days: 保留天数
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        self.errors = [
            e for e in self.errors 
            if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff
        ]
        
        self._save_errors()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取错误统计"""
        type_counts = {}
        for error in self.errors:
            error_type = error.get('type', 'unknown')
            type_counts[error_type] = type_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.errors),
            'by_type': type_counts
        }
