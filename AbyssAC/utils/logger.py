"""AbyssAC日志系统模块

提供统一的日志记录功能，支持文件和控制台输出。
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class AbyssLogger:
    """AbyssAC专用日志管理器"""
    
    _instance: Optional['AbyssLogger'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_dir: str = "storage/system/logs", name: str = "abyssac"):
        if self._initialized:
            return
        
        self.log_dir = log_dir
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建格式化器
        self.formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 添加控制台处理器
        self._add_console_handler()
        
        # 添加文件处理器
        self._add_file_handler()
        
        self._initialized = True
    
    def _add_console_handler(self) -> None:
        """添加控制台日志处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self) -> None:
        """添加文件日志处理器"""
        log_file = os.path.join(
            self.log_dir,
            f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """记录调试日志"""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """记录信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """记录错误日志"""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """记录严重错误日志"""
        self.logger.critical(message)
    
    def navigation(self, user_input: str, path: list, final_node: str, 
                   steps: int, decisions: list) -> None:
        """记录导航日志"""
        nav_log = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "user_input": user_input,
            "navigation_path": path,
            "final_node": final_node,
            "navigation_steps": steps,
            "step_decisions": decisions
        }
        
        nav_log_file = os.path.join(
            self.log_dir,
            f"navigation_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        
        import json
        with open(nav_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(nav_log, ensure_ascii=False) + '\n')
    
    def dmn(self, task_type: str, status: str, details: dict) -> None:
        """记录DMN任务日志"""
        dmn_log = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "task_type": task_type,
            "status": status,
            "details": details
        }
        
        dmn_log_file = os.path.join(
            self.log_dir,
            f"dmn_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        
        import json
        with open(dmn_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(dmn_log, ensure_ascii=False) + '\n')


def get_logger(log_dir: str = "storage/system/logs") -> AbyssLogger:
    """获取日志管理器实例"""
    return AbyssLogger(log_dir)
