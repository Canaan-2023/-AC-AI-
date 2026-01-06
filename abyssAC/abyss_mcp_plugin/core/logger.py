#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - MCP架构日志管理
"""

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class AbyssLogger:
    """
    渊协议专用日志系统
    
    提供结构化的日志记录，支持多种输出格式和级别。
    """
    
    def __init__(self, name: str = "AbyssMCP", log_dir: str = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # 日志目录
        self.log_dir = Path(log_dir or "./abyss_mcp_data/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
        
        # 结构化日志缓存
        self.structured_logs = []
        self.max_structured_logs = 1000
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 创建格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        detailed_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # 错误文件处理器
        error_file = self.log_dir / f"{self.name}_error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """信息日志"""
        self.logger.info(message)
        if extra:
            self._log_structured('INFO', message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """警告日志"""
        self.logger.warning(message)
        if extra:
            self._log_structured('WARNING', message, extra)
    
    def error(self, message: str, exc_info: bool = False, extra: Optional[Dict[str, Any]] = None):
        """错误日志"""
        self.logger.error(message, exc_info=exc_info)
        if extra:
            self._log_structured('ERROR', message, extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """调试日志"""
        self.logger.debug(message)
        if extra:
            self._log_structured('DEBUG', message, extra)
    
    def critical(self, message: str, exc_info: bool = False, extra: Optional[Dict[str, Any]] = None):
        """严重错误日志"""
        self.logger.critical(message, exc_info=exc_info)
        if extra:
            self._log_structured('CRITICAL', message, extra)
    
    def _log_structured(self, level: str, message: str, extra: Dict[str, Any]):
        """记录结构化日志"""
        structured_log = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'logger': self.name,
            'message': message,
            'extra': extra
        }
        
        self.structured_logs.append(structured_log)
        
        # 限制缓存大小
        if len(self.structured_logs) > self.max_structured_logs:
            self.structured_logs.pop(0)
    
    def get_structured_logs(self, level: Optional[str] = None, 
                           since: Optional[datetime] = None,
                           limit: int = 100) -> list:
        """获取结构化日志"""
        filtered_logs = []
        
        for log in reversed(self.structured_logs):
            # 级别过滤
            if level and log['level'] != level:
                continue
            
            # 时间过滤
            if since:
                log_time = datetime.fromisoformat(log['timestamp'])
                if log_time < since:
                    continue
            
            filtered_logs.append(log)
            
            if len(filtered_logs) >= limit:
                break
        
        return list(reversed(filtered_logs))
    
    def export_logs(self, output_file: str, level: str = 'INFO'):
        """导出日志到文件"""
        try:
            logs = self.get_structured_logs(level=level, limit=10000)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            self.error(f"日志导出失败: {e}")
            return False
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)
            
            for log_file in self.log_dir.glob(f"{self.name}_*.log"):
                if log_file.is_file() and log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
            
            return True
        except Exception as e:
            self.error(f"日志清理失败: {e}")
            return False


# 性能监控装饰器
def log_performance(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        logger = AbyssLogger(f"{func.__module__}.{func.__name__}")
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.debug(f"函数执行完成", extra={
                'function': func.__name__,
                'duration_seconds': duration,
                'status': 'success'
            })
            
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"函数执行失败", extra={
                'function': func.__name__,
                'duration_seconds': duration,
                'status': 'error',
                'error': str(e)
            })
            
            raise
    
    return wrapper