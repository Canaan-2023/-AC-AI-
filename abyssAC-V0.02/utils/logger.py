#!/usr/bin/env python3
"""
日志系统模块
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from config.config_manager import config_manager

class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class ColorFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLOR_CODES = {
        logging.DEBUG: "\033[36m",      # 青色
        logging.INFO: "\033[32m",       # 绿色
        logging.WARNING: "\033[33m",    # 黄色
        logging.ERROR: "\033[31m",      # 红色
        logging.CRITICAL: "\033[41m"    # 红底白字
    }
    
    RESET_CODE = "\033[0m"
    
    def format(self, record):
        # 添加颜色
        color_code = self.COLOR_CODES.get(record.levelno, "")
        reset_code = self.RESET_CODE if color_code else ""
        
        # 格式化消息
        record.levelname = f"{color_code}{record.levelname}{reset_code}"
        record.msg = f"{color_code}{record.msg}{reset_code}"
        
        return super().format(record)

class FileRotationHandler:
    """文件轮转处理器"""
    
    def __init__(self, log_dir: str, max_size_mb: int = 10, backup_count: int = 5):
        self.log_dir = Path(log_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
        self.current_file = None
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_current_logfile(self):
        """获取当前日志文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"abyss_{today}.log"
    
    def rotate_if_needed(self):
        """如果需要则轮转日志文件"""
        logfile = self.get_current_logfile()
        
        if logfile.exists() and logfile.stat().st_size > self.max_size_bytes:
            self.perform_rotation()
    
    def perform_rotation(self):
        """执行日志轮转"""
        logfile = self.get_current_logfile()
        timestamp = datetime.now().strftime("%H%M%S")
        
        # 重命名当前日志文件
        rotated_file = logfile.with_suffix(f".{timestamp}.log")
        if logfile.exists():
            logfile.rename(rotated_file)
        
        # 清理旧日志文件
        self.cleanup_old_logs()
    
    def cleanup_old_logs(self):
        """清理旧的日志文件"""
        log_files = sorted(self.log_dir.glob("abyss_*.log"), 
                          key=lambda x: x.stat().st_mtime, 
                          reverse=True)
        
        # 保留指定数量的文件
        for old_file in log_files[self.backup_count:]:
            try:
                old_file.unlink()
            except Exception:
                pass

class AbyssLogger:
    """渊协议日志系统"""
    
    def __init__(self, name: str = "abyss", config=None):
        self.config = config or config_manager.config
        self.logger = logging.getLogger(name)
        
        # 设置日志级别
        log_level = LogLevel[self.config.log_level].value
        self.logger.setLevel(log_level)
        
        # 移除已有处理器
        self.logger.handlers.clear()
        
        # 添加控制台处理器
        self._add_console_handler()
        
        # 如果启用文件日志，添加文件处理器
        if self.config.file_logging:
            self._add_file_handler()
        
        # 添加错误处理器
        self._add_error_handler()
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        
        # 设置格式化器
        formatter = ColorFormatter(
            fmt="%(asctime)s | %(levelname)8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        
        # 添加到logger
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """添加文件处理器"""
        # 确保日志目录存在
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建文件处理器
        log_file = log_dir / f"abyss_{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        # 设置格式化器（无颜色）
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        
        # 添加到logger
        self.logger.addHandler(file_handler)
    
    def _add_error_handler(self):
        """添加错误处理器"""
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            fmt="🚨 [ERROR] %(asctime)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        error_handler.setFormatter(formatter)
        
        self.logger.addHandler(error_handler)
    
    def debug(self, msg: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """错误日志"""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """严重错误日志"""
        self.logger.critical(msg, *args, **kwargs)
    
    def log_operation(self, operation: str, data: Dict = None):
        """记录系统操作"""
        log_data = {
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        self.info(f"操作记录: {operation} - {json.dumps(log_data, ensure_ascii=False)}")
    
    def log_cognitive_event(self, event_type: str, event_data: Dict):
        """记录认知事件"""
        event_log = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": event_data
        }
        
        log_file = Path(self.config.log_dir) / "cognitive_events.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_log, ensure_ascii=False) + "\n")
    
    def get_log_stats(self) -> Dict:
        """获取日志统计"""
        log_dir = Path(self.config.log_dir)
        
        if not log_dir.exists():
            return {"total_files": 0, "total_size": 0}
        
        log_files = list(log_dir.glob("*.log"))
        
        total_size = sum(f.stat().st_size for f in log_files if f.exists())
        
        return {
            "total_files": len(log_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "log_dir": str(log_dir)
        }

def setup_logging(config=None):
    """设置全局日志"""
    config = config or config_manager.config
    
    # 创建主logger
    main_logger = AbyssLogger("abyss", config)
    
    # 设置第三方库的日志级别
    logging.getLogger("jieba").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return main_logger

# 全局logger实例
logger = setup_logging()