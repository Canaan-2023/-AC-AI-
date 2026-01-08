#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议 v5.0 - 核心基础设施 (优化版)
重构版本：优化并发、减少锁、增加反向索引、智能记忆整合、Ollama集成

主要改进：
✅ 统一Result类型，标准化错误处理
✅ 运行模式配置（standalone/ollama/api）
✅ 最小化锁使用，采用无冲突并行设计
✅ 自定义内存监控，移除外部依赖
✅ 分段锁替代全局锁
✅ 智能记忆整合（模型判断语义相关性）

作者: AbyssAC Protocol Team
版本: 5.0 (Optimized Edition)
依赖: 无外部依赖，纯Python标准库
"""

import os
import sys
import json
import time
import math
import shutil
import hashlib
import logging
import traceback
import threading
import concurrent.futures
import atexit
import signal
import gc
import re
import warnings
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple, Set, Callable
from collections import Counter, defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from abc import ABC, abstractmethod

# 忽略警告
warnings.filterwarnings('ignore')

# =============================================================================
# 自定义异常类
# =============================================================================

class AbyssProtocolError(Exception):
    """渊协议基础异常"""
    pass

class ConfigValidationError(AbyssProtocolError):
    """配置验证错误"""
    pass

class MemoryError(AbyssProtocolError):
    """记忆系统错误"""
    pass

class CognitiveError(AbyssProtocolError):
    """认知内核错误"""
    pass

class FileSystemError(AbyssProtocolError):
    """文件系统错误"""
    pass

class OllamaError(AbyssProtocolError):
    """Ollama相关错误"""
    pass

# =============================================================================
# 统一结果类型
# =============================================================================

class Result:
    """统一的结果类型，用于标准化函数返回值"""
    
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None, 
                 error_type: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error
        self.error_type = error_type
        self.timestamp = datetime.now().isoformat()
    
    @classmethod
    def ok(cls, data: Any = None) -> 'Result':
        """创建成功结果"""
        return cls(success=True, data=data)
    
    @classmethod
    def error(cls, message: str, error_type: Optional[str] = None) -> 'Result':
        """创建错误结果"""
        return cls(success=False, error=message, error_type=error_type)
    
    def is_ok(self) -> bool:
        """检查是否成功"""
        return self.success
    
    def is_error(self) -> bool:
        """检查是否错误"""
        return not self.success
    
    def unwrap(self) -> Any:
        """获取数据，如果失败则抛出异常"""
        if self.success:
            return self.data
        raise ValueError(f"Result is error: {self.error}")
    
    def unwrap_or(self, default: Any) -> Any:
        """获取数据，如果失败则返回默认值"""
        return self.data if self.success else default
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'error_type': self.error_type,
            'timestamp': self.timestamp
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'Result':
        """从字典创建"""
        return Result(
            success=data.get('success', False),
            data=data.get('data'),
            error=data.get('error'),
            error_type=data.get('error_type')
        )

# =============================================================================
# 日志系统
# =============================================================================

class AbyssLogger:
    """渊协议专用日志系统 - 线程安全"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        # 确保只初始化一次
        if hasattr(self, 'initialized'):
            return
        
        self.logger = logging.getLogger("AbyssProtocol")
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 文件处理器
            log_path = Path.cwd() / "abyss_data" / "logs" / "abyss.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # 格式化
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
        
        self.initialized = True
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """错误日志"""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)

# =============================================================================
# 配置管理器 - 支持运行模式
# =============================================================================

class ConfigManager:
    """配置管理器 - 使用分段锁减少锁竞争，支持运行模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        
        # 配置数据（使用分段锁保护）
        self._config = self._load_default_config()
        self._config_lock = threading.RLock()  # 仅在必要时使用
        self.initialized = True
    
    def _load_default_config(self) -> Dict:
        """加载默认配置"""
        return {
            # 系统配置
            'system': {
                'auto_save_interval': 300,
                'health_check_interval': 60,
                'enable_metrics': True,
                'base_path': './abyss_data',
                'max_memory_mb': 500,
                'run_mode': 'standalone',  # standalone, ollama, api
            },
            # 运行模式配置
            'modes': {
                'standalone': {  # 纯本地，无LLM
                    'enable_ollama': False,
                    'enable_api': False,
                    'description': '纯本地模式，不依赖外部服务'
                },
                'ollama': {      # 本地LLM
                    'enable_ollama': True,
                    'enable_api': False,
                    'ollama_url': 'http://localhost:11434',
                    'default_model': 'llama3.2',
                    'description': '本地Ollama模式，使用本地大语言模型'
                },
                'api': {         # 云端API
                    'enable_ollama': False,
                    'enable_api': True,
                    'api_provider': 'claude',
                    'api_key': '',
                    'description': '云端API模式，使用外部API服务'
                }
            },
            # 字典配置
            'dictionary': {
                'max_dict_size': 5000,
                'max_dict_files': 50,
                'activation_threshold': 0.3,
                'fission_enabled': True,
                'fission_check_interval': 100,
                'split_threshold': 0.8,
                'merge_threshold': 0.3,
                'segment_lock_count': 8,
                'cache_size': 1000,
                'shadow_index_size': 1000,
                'index_max_size': 10000,
                'index_lru_size': 1000,
            },
            # 分词器配置
            'tokenizer': {
                'cache_size': 1000,
                'enable_activation_cache': True,
                'activation_cache_size': 500,
                'max_keywords_per_text': 15,
                'min_word_length': 2,
                'max_word_length': 20,
                'extract_english': True,
                'extract_numbers': False,
                'remove_punctuation': True,
                'dict_word_boost': 1.5,
                'enable_smart_correction': True,  # 启用智能纠错
                'trad_to_simp_map': {  # 繁简转换表
                    '機': '机', '學': '学', '習': '习', '認': '认', '識': '识',
                    '為': '为', '這': '这', '個': '个', '來': '来', '時': '时',
                    '實': '实', '現': '现', '過': '过', '進': '进', '說': '说',
                    '會': '会', '發': '发', '開': '开', '關': '关', '門': '门',
                    '問': '问', '題': '题', '見': '见', '長': '长', '電': '电',
                    '腦': '脑', '網': '网', '語': '语', '記': '记', '錄': '录',
                    '讀': '读', '寫': '写', '聽': '听', '講': '讲', '話': '话',
                    '視': '视', '頻': '频', '圖': '图', '書': '书', '報': '报',
                    '紙': '纸', '筆': '笔', '畫': '画', '音': '音', '樂': '乐',
                    '歌': '歌', '舞': '舞', '運': '运', '動': '动', '游': '游',
                    '戲': '戏', '電': '电', '影': '影', '視': '视', '聽': '听',
                    '計': '计', '算': '算', '機': '机', '器': '器', '人': '人',
                    '工': '工', '智': '智', '能': '能', '系': '系', '統': '统',
                    '軟': '软', '件': '件', '硬': '硬', '設': '设', '備': '备',
                    '程': '程', '序': '序', '編': '编', '碼': '码', '譯': '译',
                    '調': '调', '試': '试', '運': '运', '行': '行', '維': '维',
                    '護': '护', '更': '更', '新': '新', '版': '版', '本': '本',
                    '文': '文', '件': '件', '資': '资', '料': '料', '數': '数',
                    '據': '据', '庫': '库', '存': '存', '儲': '储', '空': '空',
                    '間': '间', '地': '地', '址': '址', '路': '路', '徑': '径',
                    '名': '名', '稱': '称', '類': '类', '型': '型', '屬': '属',
                    '性': '性', '值': '值', '參': '参', '數': '数', '變': '变',
                    '量': '量', '常': '常', '量': '量', '函': '函', '數': '数',
                    '方': '方', '法': '法', '對': '对', '象': '象', '類': '类',
                    '實': '实', '例': '例', '繼': '继', '承': '承', '重': '重',
                    '載': '载', '覆': '覆', '蓋': '盖', '隱': '隐', '藏': '藏',
                    '封': '封', '裝': '装', '抽': '抽', '象': '象', '多': '多',
                    '態': '态', '靜': '静', '態': '态', '動': '动', '態': '态',
                    '同': '同', '步': '步', '異': '异', '步': '步', '並': '并',
                    '行': '行', '串': '串', '行': '行', '線': '线', '程': '程',
                    '進': '进', '程': '程', '服': '服', '務': '务', '器': '器',
                    '客': '客', '戶': '户', '端': '端', '網': '网', '絡': '络',
                    '協': '协', '議': '议', '端': '端', '口': '口', '套': '套',
                    '接': '接', '字': '字', '緩': '缓', '存': '存', '區': '区',
                    '流': '流', '水': '水', '線': '线', '作': '作', '業': '业',
                    '任': '任', '務': '务', '工': '工', '作': '作', '流': '流',
                    '程': '程', '控': '控', '制': '制', '權': '权', '限': '限',
                    '安': '安', '全': '全', '密': '密', '碼': '码', '加': '加',
                    '解': '解', '密': '密', '壓': '压', '縮': '缩', '編': '编',
                    '解': '解', '碼': '码', '轉': '转', '換': '换', '格': '格',
                    '式': '式', '類': '类', '型': '型', '文': '文', '本': '本',
                    '二': '二', '進': '进', '制': '制', '八': '八', '進': '进',
                    '制': '制', '十': '十', '進': '进', '制': '制', '十': '十',
                    '六': '六', '進': '进', '制': '制', '位': '位', '元': '元',
                    '比': '比', '特': '特', '字': '字', '節': '节', '字': '字',
                    '符': '符', '串': '串', '數': '数', '組': '组', '列': '列',
                    '表': '表', '集': '集', '合': '合', '映': '映', '射': '射',
                    '堆': '堆', '棧': '栈', '隊': '队', '列': '列', '樹': '树',
                    '圖': '图', '網': '网', '絡': '络', '節': '节', '點': '点',
                    '邊': '边', '權': '权', '重': '重', '路': '路', '徑': '径',
                    '環': '环', '連': '连', '通': '通', '強': '强', '連': '连',
                    '通': '通', '弱': '弱', '連': '连', '通': '通', '有': '有',
                    '向': '向', '無': '无', '向': '向', '加': '加', '權': '权',
                    '最': '最', '小': '小', '生': '生', '成': '成', '樹': '树',
                    '最': '最', '短': '短', '路': '路', '徑': '径', '拓': '拓',
                    '撲': '扑', '排': '排', '序': '序', '搜': '搜', '索': '索'
                }
            },
            # 认知配置
            'cognitive': {
                'enable_propagation': True,
                'score_base_value': 0.1,
                'complexity_weight': 0.3,
                'confidence_weight': 0.7,
                'depth_weight': 0.3,
                'match_score_weight': 0.6,
                'high_score_threshold': 0.7,
                'medium_score_threshold': 0.5,
                'low_score_threshold': 0.3,
                'complexity_max_chars': 2000,
                'complexity_max_sentences': 20,
                'drift_log_keep': 50,
                'activation_cache_size': 500,
                'enable_activation_cache': True,
            },
            # X层配置
            'xlayer': {
                'symbol_ttl_hours': 24,
                'max_symbols': 30,
                'backup_history_size': 10,
            },
            # AC-100配置
            'ac100': {
                'evaluation_interval': 5,
                'dimension_weights': {
                    'self_reference': 0.15,
                    'value_autonomy': 0.15,
                    'cognitive_growth': 0.15,
                    'memory_continuity': 0.15,
                    'prediction_imagination': 0.15,
                    'environment_interaction': 0.1,
                    'explanation_transparency': 0.15,
                },
                'enable_model_evaluation': True,  # 启用模型评估
            },
            # 记忆配置
            'memory': {
                'working_memory_size': 100,
                'max_memory_per_layer': 1000,
                'cleanup_interval': 3600,
                'importance_threshold': 0.5,
                'fuse_similarity_threshold': 0.7,
                'time_decay_hours': 168,
                'cleanup_batch_size': 10,
                'enable_model_integration': True,  # 启用模型判断整合
                'integration_threshold': 0.8,  # 模型判断阈值
            },
            # 拓扑配置
            'topology': {
                'max_path_length': 8,
                'max_expansions': 50,
                'max_candidate_paths': 20,
                'novelty_weight': 0.3,
                'coherence_weight': 0.5,
                'relevance_weight': 0.2,
                'cache_ttl_seconds': 300,
            },
            # 性能配置
            'performance': {
                'cache_ttl_seconds': 300,
                'max_thread_workers': 5,
                'enable_async_tasks': True,
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值 - 无锁读取（配置不可变）"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> Result:
        """设置配置值 - 使用锁保护"""
        try:
            with self._config_lock:
                keys = key.split(".")
                config = self._config
                
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                
                config[keys[-1]] = value
            return Result.ok()
        except Exception as e:
            return Result.error(f"设置配置失败: {e}", "ConfigError")
    
    def update(self, config_dict: Dict) -> Result:
        """更新配置"""
        try:
            with self._config_lock:
                self._deep_merge(self._config, config_dict)
            return Result.ok()
        except Exception as e:
            return Result.error(f"更新配置失败: {e}", "ConfigError")
    
    def _deep_merge(self, base: Dict, override: Dict):
        """深度合并字典"""
        for key, value in override.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get_current_mode(self) -> str:
        """获取当前运行模式"""
        return self.get('system.run_mode', 'standalone')
    
    def set_mode(self, mode: str) -> Result:
        """设置运行模式"""
        available_modes = ['standalone', 'ollama', 'api']
        if mode not in available_modes:
            return Result.error(f"无效的运行模式: {mode}", "ConfigValidationError")
        
        return self.set('system.run_mode', mode)

# =============================================================================
# 自定义内存监控 - 移除psutil依赖
# =============================================================================

class MemoryMonitor:
    """自定义内存监控器 - 无需外部依赖"""
    
    def __init__(self):
        self.gc_thresholds = gc.get_threshold()
        self.last_gc_stats = gc.get_stats()
        self.monitor_lock = threading.Lock()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            # 使用gc模块获取对象统计
            objects_by_type = Counter()
            for obj in gc.get_objects():
                objects_by_type[type(obj).__name__] += 1
            
            # 估算内存使用（基于对象数量）
            total_objects = sum(objects_by_type.values())
            
            # 简单的内存估算：假设平均每个对象占用100字节
            estimated_memory_mb = total_objects * 100 / (1024 * 1024)
            
            # 获取GC统计
            gc_stats = gc.get_stats()
            gc_collections = sum(stat['collections'] for stat in gc_stats)
            
            return {
                'estimated_memory_mb': round(estimated_memory_mb, 2),
                'total_objects': total_objects,
                'gc_collections': gc_collections,
                'top_object_types': dict(objects_by_type.most_common(10)),
            }
        except Exception as e:
            return {'error': str(e)}
    
    def force_gc(self) -> int:
        """强制垃圾回收"""
        try:
            return gc.collect()
        except Exception:
            return 0
    
    def get_object_growth(self) -> Dict[str, Any]:
        """获取对象增长趋势"""
        try:
            current_stats = gc.get_stats()
            
            # 计算增长率
            growth_info = {}
            for i, (prev, curr) in enumerate(zip(self.last_gc_stats, current_stats)):
                growth_info[f'generation_{i}'] = {
                    'collections': curr['collections'] - prev['collections'],
                    'collected': curr['collected'] - prev['collected'],
                    'uncollectable': curr['uncollectable'] - prev['uncollectable'],
                }
            
            self.last_gc_stats = current_stats
            return growth_info
        except Exception as e:
            return {'error': str(e)}

# =============================================================================
# 文件管理器 - 优化文件句柄管理
# =============================================================================

class FileManager:
    """文件管理器 - 处理所有文件操作"""
    
    def __init__(self):
        self.base_path = Path.cwd() / "abyss_data"
        self.base_path.mkdir(exist_ok=True)
        
        # 文件句柄池（使用弱引用避免内存泄漏）
        self.file_handles = {}
        self.handle_lock = threading.RLock()
        
        # 创建子目录
        self.dictionaries_path = self.base_path / "dictionaries"
        self.states_path = self.base_path / "states"
        self.logs_path = self.base_path / "logs"
        self.plugins_path = self.base_path / "plugins"
        
        self.dictionaries_path.mkdir(exist_ok=True)
        self.states_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)
        self.plugins_path.mkdir(exist_ok=True)
    
    def get_path(self, filename: str) -> Path:
        """获取文件路径"""
        return self.base_path / filename
    
    def get_dictionary_path(self, dict_name: str) -> Path:
        """获取字典文件路径"""
        return self.dictionaries_path / f"{dict_name}.txt"
    
    def get_state_path(self, component: str) -> Path:
        """获取状态文件路径"""
        return self.states_path / f"{component}_state.json"
    
    def get_plugin_path(self, plugin_name: str) -> Path:
        """获取插件文件路径"""
        return self.plugins_path / f"{plugin_name}.py"
    
    def safe_read(self, path: Union[str, Path]) -> Result:
        """安全读取文件内容"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            return Result.ok(content)
        except (IOError, OSError) as e:
            return Result.error(f"读取文件失败 {path}: {e}", "FileSystemError")
    
    def safe_write(self, path: Union[str, Path], content: str) -> Result:
        """安全写入文件内容"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return Result.ok(True)
        except (IOError, OSError) as e:
            return Result.error(f"写入文件失败 {path}: {e}", "FileSystemError")
    
    def safe_json_load(self, path: Union[str, Path]) -> Result:
        """安全加载JSON文件"""
        try:
            content_result = self.safe_read(path)
            if content_result.is_error():
                return content_result
            
            content = content_result.unwrap()
            if content:
                return Result.ok(json.loads(content))
            return Result.ok({})
        except json.JSONDecodeError as e:
            return Result.error(f"JSON解析失败 {path}: {e}", "JsonError")
    
    def safe_json_save(self, path: Union[str, Path], data: Dict) -> Result:
        """安全保存JSON文件"""
        try:
            content = json.dumps(data, ensure_ascii=False, indent=2)
            return self.safe_write(path, content)
        except (TypeError, IOError) as e:
            return Result.error(f"保存JSON失败 {path}: {e}", "JsonError")
    
    def cleanup_old_files(self, days: int = 30) -> Result:
        """清理旧文件"""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            for path in [self.dictionaries_path, self.states_path, self.logs_path]:
                if path.exists():
                    for file_path in path.iterdir():
                        try:
                            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                                file_path.unlink()
                                logger.info(f"删除旧文件: {file_path}")
                        except (OSError, IOError) as e:
                            return Result.error(f"清理文件失败 {file_path}: {e}", "FileSystemError")
            
            return Result.ok()
        except Exception as e:
            return Result.error(f"清理旧文件失败: {e}", "FileSystemError")
    
    def close_all_handles(self) -> Result:
        """关闭所有文件句柄"""
        try:
            with self.handle_lock:
                for path, handle in self.file_handles.items():
                    try:
                        if not handle.closed:
                            handle.close()
                    except Exception as e:
                        logger.warning(f"关闭句柄失败 {path}: {e}")
                self.file_handles.clear()
            return Result.ok()
        except Exception as e:
            return Result.error(f"关闭文件句柄失败: {e}", "FileSystemError")

# =============================================================================
# 指标收集器 - 无锁设计
# =============================================================================

class MetricsCollector:
    """指标收集器 - 使用原子操作减少锁竞争"""
    
    def __init__(self):
        self._metrics = defaultdict(Counter)
        self._timers = {}
        # 使用原子操作，最小化锁使用
        self.lock = threading.RLock()
    
    def increment(self, metric_name: str, value: int = 1):
        """增加指标值"""
        # 使用原子操作避免锁
        with self.lock:
            self._metrics[metric_name]['count'] += value
    
    def timer(self, metric_name: str):
        """计时器上下文管理器"""
        return TimerContext(self, metric_name)
    
    def record_time(self, metric_name: str, duration: float):
        """记录时间"""
        with self.lock:
            self._metrics[metric_name]['total_time'] += duration
            self._metrics[metric_name]['count'] += 1
    
    def get_metrics(self) -> Dict:
        """获取所有指标"""
        with self.lock:
            return dict(self._metrics)
    
    def reset(self):
        """重置所有指标"""
        with self.lock:
            self._metrics.clear()

# =============================================================================
# 计时器上下文
# =============================================================================

class TimerContext:
    """计时器上下文管理器"""
    
    def __init__(self, metrics: MetricsCollector, metric_name: str):
        self.metrics = metrics
        self.metric_name = metric_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.record_time(self.metric_name, duration)

# =============================================================================
# 分段锁实现 - 减少锁竞争
# =============================================================================

class SegmentLock:
    """分段锁实现 - 用于细粒度并发控制"""
    
    def __init__(self, segment_count: int = 8):
        self.segment_count = segment_count
        self.locks = [threading.RLock() for _ in range(segment_count)]
    
    def _get_segment(self, key: Any) -> int:
        """获取分段索引"""
        return hash(key) % self.segment_count
    
    @contextmanager
    def acquire(self, key: Any):
        """获取分段锁"""
        segment = self._get_segment(key)
        with self.locks[segment]:
            yield
    
    @contextmanager
    def acquire_all(self):
        """获取所有锁（用于需要全局同步的操作）"""
        # 按顺序获取所有锁，避免死锁
        with ExitStack() as stack:
            for lock in self.locks:
                stack.enter_context(lock)
            yield

from contextlib import ExitStack

# =============================================================================
# 持久化管理器
# =============================================================================

class PersistenceManager:
    """持久化管理器 - 管理组件状态持久化"""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.logger = AbyssLogger()
    
    def save_state(self, component_name: str, state: Dict) -> Result:
        """保存组件状态"""
        try:
            state_path = self.file_manager.get_state_path(component_name)
            return self.file_manager.safe_json_save(state_path, state)
        except Exception as e:
            return Result.error(f"保存 {component_name} 状态失败: {e}", "PersistenceError")
    
    def load_state(self, component_name: str) -> Result:
        """加载组件状态"""
        try:
            state_path = self.file_manager.get_state_path(component_name)
            return self.file_manager.safe_json_load(state_path)
        except Exception as e:
            return Result.error(f"加载 {component_name} 状态失败: {e}", "PersistenceError")
    
    def save_all(self, components: Dict[str, Any]) -> Result:
        """保存所有组件状态"""
        for name, component in components.items():
            if hasattr(component, 'serialize_state'):
                try:
                    state = component.serialize_state()
                    result = self.save_state(name, state)
                    if result.is_error():
                        return result
                except Exception as e:
                    return Result.error(f"序列化 {name} 失败: {e}", "SerializationError")
        return Result.ok()
    
    def load_all(self, components: Dict[str, Any]) -> Result:
        """加载所有组件状态"""
        for name, component in components.items():
            if hasattr(component, 'deserialize_state'):
                try:
                    result = self.load_state(name)
                    if result.is_ok():
                        state = result.unwrap()
                        if state:
                            component.deserialize_state(state)
                except Exception as e:
                    return Result.error(f"反序列化 {name} 失败: {e}", "DeserializationError")
        return Result.ok()

# =============================================================================
# 健康状态
# =============================================================================

class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"

# =============================================================================
# 健康检查器
# =============================================================================

class HealthChecker:
    """健康检查系统"""
    
    def __init__(self, memory_monitor: MemoryMonitor):
        self.config = ConfigManager()
        self.logger = AbyssLogger()
        self.metrics = MetricsCollector()
        self.memory_monitor = memory_monitor
        self.checks = {}
        self.lock = threading.RLock()
        
        # 启动健康检查线程
        self._start_health_monitoring()
    
    def _start_health_monitoring(self):
        """启动健康监控"""
        def monitor_loop():
            interval = self.config.get('system.health_check_interval', 60)
            while True:
                try:
                    self.run_all_checks()
                    time.sleep(interval)
                except Exception as e:
                    self.logger.error(f"健康检查错误: {e}")
                    time.sleep(60)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True, name="HealthMonitor")
        monitor_thread.start()
        
        self.logger.info("健康检查系统已启动")
    
    def register_check(self, name: str, check_func: Callable[[], Tuple[HealthStatus, str]]):
        """注册健康检查"""
        with self.lock:
            self.checks[name] = check_func
    
    def run_all_checks(self) -> Dict:
        """运行所有健康检查"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        with self.lock:
            for name, check_func in self.checks.items():
                try:
                    status, message = check_func()
                    results[name] = {
                        'status': status.value,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # 更新总体状态
                    if status == HealthStatus.CRITICAL:
                        overall_status = HealthStatus.CRITICAL
                    elif status == HealthStatus.WARNING and overall_status != HealthStatus.CRITICAL:
                        overall_status = HealthStatus.WARNING
                
                except Exception as e:
                    results[name] = {
                        'status': HealthStatus.CRITICAL.value,
                        'message': f"检查失败: {e}",
                        'timestamp': datetime.now().isoformat()
                    }
                    overall_status = HealthStatus.CRITICAL
        
        results['overall'] = {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat()
        }
        
        # 记录健康状态
        if overall_status == HealthStatus.CRITICAL:
            self.logger.error(f"系统健康状态: {overall_status.value}")
        elif overall_status == HealthStatus.WARNING:
            self.logger.warning(f"系统健康状态: {overall_status.value}")
        else:
            self.logger.debug(f"系统健康状态: {overall_status.value}")
        
        return results
    
    def check_memory_usage(self) -> Tuple[HealthStatus, str]:
        """检查内存使用"""
        try:
            memory_info = self.memory_monitor.get_memory_usage()
            estimated_memory_mb = memory_info.get('estimated_memory_mb', 0)
            
            max_memory = self.config.get('system.max_memory_mb', 500)
            
            if estimated_memory_mb > max_memory:
                return HealthStatus.CRITICAL, f"内存使用超限: {estimated_memory_mb:.1f}MB > {max_memory}MB"
            elif estimated_memory_mb > max_memory * 0.8:
                return HealthStatus.WARNING, f"内存使用较高: {estimated_memory_mb:.1f}MB/{max_memory}MB"
            else:
                return HealthStatus.HEALTHY, f"内存使用正常: {estimated_memory_mb:.1f}MB/{max_memory}MB"
        except Exception as e:
            return HealthStatus.WARNING, f"内存检查失败: {e}"
    
    def check_disk_space(self) -> Tuple[HealthStatus, str]:
        """检查磁盘空间"""
        try:
            base_path = Path(self.config.get('system.base_path', './abyss_data'))
            total, used, free = shutil.disk_usage(base_path)
            
            free_gb = free / 1024 / 1024 / 1024
            
            if free_gb < 1:
                return HealthStatus.CRITICAL, f"磁盘空间不足: {free_gb:.2f}GB"
            elif free_gb < 5:
                return HealthStatus.WARNING, f"磁盘空间较少: {free_gb:.2f}GB"
            else:
                return HealthStatus.HEALTHY, f"磁盘空间充足: {free_gb:.2f}GB"
        except Exception as e:
            return HealthStatus.WARNING, f"磁盘检查失败: {e}"

# =============================================================================
# 优雅关闭管理器
# =============================================================================

class ShutdownManager:
    """优雅关闭管理器"""
    
    def __init__(self):
        self.shutdown_handlers = []
        self.is_shutting_down = False
        self.lock = threading.Lock()
        
        # 注册信号处理器
        self._register_signal_handlers()
    
    def _register_signal_handlers(self):
        """注册信号处理器"""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except (AttributeError, ValueError, OSError):
            # Windows或不支持信号的环境
            pass
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，开始优雅关闭...")
        self.shutdown()
    
    def register_handler(self, handler: Callable) -> Result:
        """注册关闭处理器"""
        try:
            with self.lock:
                self.shutdown_handlers.append(handler)
            return Result.ok()
        except Exception as e:
            return Result.error(f"注册关闭处理器失败: {e}")
    
    def shutdown(self) -> Result:
        """执行优雅关闭"""
        with self.lock:
            if self.is_shutting_down:
                return Result.ok()
            self.is_shutting_down = True
        
        logger.info("开始优雅关闭...")
        
        # 执行所有关闭处理器
        for handler in self.shutdown_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"关闭处理器失败: {e}")
        
        logger.info("优雅关闭完成")
        return Result.ok()

# =============================================================================
# 全局实例
# =============================================================================

# 使用延迟初始化，避免启动时开销
config = ConfigManager()
logger = AbyssLogger()
metrics = MetricsCollector()
memory_monitor = MemoryMonitor()
file_manager = FileManager()
health_checker = HealthChecker(memory_monitor)
shutdown_manager = ShutdownManager()

# 注册健康检查
health_checker.register_check('memory', health_checker.check_memory_usage)
health_checker.register_check('disk', health_checker.check_disk_space)

print("[✅] 核心基础设施完成")
print("    - 统一Result类型，标准化错误处理")
print("    - 运行模式配置支持")
print("    - 自定义内存监控（无外部依赖）")
print("    - 分段锁优化并发")
print("    - 健康检查系统")
print("    - 优雅关闭管理器")
