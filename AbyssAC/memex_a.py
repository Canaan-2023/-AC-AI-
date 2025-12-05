import json
import os
import logging
import shutil
import hashlib
import math
import threading
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from functools import lru_cache, wraps
from pathlib import Path
from collections import Counter, OrderedDict
import tempfile

# ===================== 日志配置 =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("memex_a.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("Memex-A-Enhanced")

# ===================== 性能监控装饰器 =====================
def log_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"⏱️ {func.__name__} 执行时间: {execution_time:.2f}秒（参数：{args[:2]}...）")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"⏱️ {func.__name__} 执行失败（耗时：{execution_time:.2f}秒）：{e}", exc_info=True)
            raise
    return wrapper

# ===================== 配置类（修复初始化问题） =====================
class Config:
    """修复：支持自定义配置路径+初始化逻辑优化"""
    DEFAULT_CONFIG = {
        "INDEX_PATH": "四层记忆关联索引.txt",
        "REVERSE_INDEX_PATH": "反向关联索引.json",
        "RETRIEVAL_COUNT_PATH": "检索次数记录.json",
        "FULL_CONTENT_DIR": "完整记忆内容",
        "BE_TOKEN_PATH": "BE_token.json",
        "USER_CONFIG_PATH": "user_config.json",
        "BACKUP_DIR": "memex_backups",
        "BE_TOKEN_EXPIRE_DAYS": 30,
        "MIN_STRENGTH_THRESHOLD": 0.7,
        "FREQUENCY_BONUS_THRESHOLD": 5,
        "FREQUENCY_BONUS_BASE": 0.05,
        "TARGETED_BONUS": 0.03,
        "EXPIRE_PENALTY": 0.05,
        "LOG_LEVEL": "INFO",
        "LEVEL_WEIGHTS": {
            "核心": 1.0,
            "元认知": 0.8,
            "工作": 0.7,
            "情感": 0.75
        },
        "DEFAULT_AC100_BASE_SCORES": {
            "self_reference": 90.0,
            "values": 95.0,
            "growth": 85.0,
            "memory_continuity": 90.0,
            "prediction": 92.0,
            "meta_block": 88.0,
            "interaction": 80.0,
            "transparency": 85.0
        },
        "DEFAULT_AC100_WEIGHTS": {
            "self_reference": 0.17,
            "values": 0.17,
            "growth": 0.14,
            "memory_continuity": 0.14,
            "prediction": 0.14,
            "meta_block": 0.10,
            "interaction": 0.07,
            "transparency": 0.07
        },
        "CACHE_MAX_SIZE": 2000,  # 新增：缓存最大容量
        "INDEX_SHARD_COUNT": 10   # 新增：索引分片数量
    }
    # 🔥 修复：允许传入自定义配置路径
    def __init__(self, config_path: str = None):
        self.__dict__.update(self.DEFAULT_CONFIG)
        # 优先加载传入的配置文件
        if config_path and os.path.exists(config_path):
            self.load_from_json(config_path)
        else:
            # 加载默认配置+用户配置
            self.load_user_config()
        self.AC100_BASE_SCORES = self._get_ac100_config("ac100_base_scores", self.DEFAULT_AC100_BASE_SCORES)
        self.AC100_WEIGHTS = self._get_ac100_config("ac100_weights", self.DEFAULT_AC100_WEIGHTS)
        self.validate_config()
        self.update_log_level()

    @classmethod
    def from_json(cls, config_path: str = "memex_config.json"):
        return cls(config_path=config_path)

    def load_from_json(self, config_path: str):
        """加载指定路径的配置文件"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                external_config = json.load(f)
            for key, value in external_config.items():
                if key in self.DEFAULT_CONFIG:
                    old_value = getattr(self, key)
                    setattr(self, key, value)
                    logger.info(f"🔄 加载配置：{key} = {old_value} → {value}")
        except Exception as e:
            logger.error(f"⚠️ 加载配置文件{config_path}失败：{e}")

    def load_user_config(self):
        if not os.path.exists(self.USER_CONFIG_PATH):
            logger.info(f"ℹ️ 未找到用户配置文件「{self.USER_CONFIG_PATH}」")
            return
        try:
            with open(self.USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            for key, value in user_config.items():
                if key in self.DEFAULT_CONFIG:
                    old_value = getattr(self, key)
                    setattr(self, key, value)
                    logger.info(f"🔄 用户配置覆盖：{key} = {old_value} → {value}")
        except Exception as e:
            logger.error(f"⚠️ 加载用户配置失败：{e}")

    def _get_ac100_config(self, key: str, default: Dict[str, float]) -> Dict[str, float]:
        user_config = {}
        if os.path.exists(self.USER_CONFIG_PATH):
            with open(self.USER_CONFIG_PATH, "r", encoding="utf-8") as f:
                user_config = json.load(f)
        if key in user_config:
            user_ac100 = user_config[key]
            missing_keys = [k for k in default if k not in user_ac100]
            if missing_keys:
                logger.warning(f"⚠️ AC-100配置缺失维度：{missing_keys}，补充默认值")
                user_ac100.update({k: default[k] for k in missing_keys})
            return user_ac100
        return default

    def validate_config(self):
        for dir_attr in ["FULL_CONTENT_DIR", "BACKUP_DIR"]:
            os.makedirs(getattr(self, dir_attr), exist_ok=True)
        numeric_checks = [
            ("BE_TOKEN_EXPIRE_DAYS", lambda x: x > 0),
            ("MIN_STRENGTH_THRESHOLD", lambda x: 0 <= x <= 1),
            ("FREQUENCY_BONUS_BASE", lambda x: 0 <= x <= 0.5),
            ("CACHE_MAX_SIZE", lambda x: x > 100),  # 新增：校验缓存容量
            ("INDEX_SHARD_COUNT", lambda x: 2 <= x <= 20)  # 新增：校验分片数量
        ]
        for key, validator in numeric_checks:
            value = getattr(self, key)
            if not validator(value):
                logger.error(f"⚠️ 配置{key}无效（{value}），恢复默认值")
                setattr(self, key, self.DEFAULT_CONFIG[key])
        weights_sum = round(sum(self.AC100_WEIGHTS.values()), 2)
        if weights_sum != 1.0:
            logger.warning(f"⚠️ AC100权重和≠1（{weights_sum}），自动归一化")
            total = sum(self.AC100_WEIGHTS.values())
            self.AC100_WEIGHTS = {k: v/total for k, v in self.AC100_WEIGHTS.items()}

    def update_log_level(self):
        log_level_map = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "ERROR": logging.ERROR}
        log_level = log_level_map.get(self.LOG_LEVEL.upper(), logging.INFO)
        logger.setLevel(log_level)
        for handler in logger.handlers:
            handler.setLevel(log_level)

# ===================== 核心类：MemexA（整合所有修复） =====================
class MemexA:
    def __init__(self, config: Config = None):
        self.config = config if config else Config()
        self.__index_cache = OrderedDict()  # 改为OrderedDict实现LRU缓存
        self.__be_token_cache = {}
        self.__batch_buffer = []
        self.__flush_threshold = 10
        self._cache_lock = threading.RLock()
        # 新增：初始化分片路径
        self.__index_shard_paths = [
            f"四层记忆关联索引_{i}.txt" for i in range(self.config.INDEX_SHARD_COUNT)
        ]
        self.init_files()
        self.load_index_cache()
        self.load_be_token_cache()
        self.get_memory_level.cache_clear()

    # ===================== 新增：核心修复方法 =====================
    def _cleanup_cache(self):
        """LRU策略清理缓存，避免内存泄漏"""
        with self._cache_lock:
            if len(self.__index_cache) <= self.config.CACHE_MAX_SIZE:
                return
            delete_count = len(self.__index_cache) - int(self.config.CACHE_MAX_SIZE * 0.8)
            for _ in range(delete_count):
                self.__index_cache.popitem(last=False)  # FIFO模拟LRU
            logger.info(f"✅ 缓存清理完成：删除{delete_count}条，剩余{len(self.__index_cache)}条")

    def _atomic_write(self, file_path: str, content: str, mode: str = "a"):
        """原子写入：避免多进程并发冲突"""
        temp_dir = os.path.dirname(file_path) or "."
        with tempfile.NamedTemporaryFile(
            dir=temp_dir, prefix="memex_temp_", suffix=".txt", delete=False
        ) as temp_f:
            if mode == "a" and os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    temp_f.write(f.read().encode("utf-8"))
            temp_f.write(content.encode("utf-8"))
            temp_path = temp_f.name
        try:
            os.replace(temp_path, file_path)
            return True
        except Exception as e:
            logger.error(f"❌ 原子写入失败（{file_path}）：{e}")
            os.remove(temp_path)
            return False

    def _get_index_shard(self, memory_id: str) -> str:
        """按记忆ID哈希分配分片路径"""
        if not memory_id.isdigit():
            return self.__index_shard_paths[0]
        shard_idx = int(memory_id) % self.config.INDEX_SHARD_COUNT
        return self.__index_shard_paths[shard_idx]

    # ===================== 原有方法：适配分片/缓存/原子写入 =====================
    def init_files(self):
        try:
            dirs = [self.config.FULL_CONTENT_DIR, self.config.BACKUP_DIR, os.path.join(".", "Y_OCR库")]
            for dir_path in dirs:
                os.makedirs(dir_path, exist_ok=True)
            y_levels = ["核心记忆", "元认知记忆", "工作记忆", "情感记忆"]
            for level in y_levels:
                os.makedirs(os.path.join(".", "Y_OCR库", level), exist_ok=True)
            core_files = [
                (self.__index_shard_paths[0], self._init_index_file),  # 初始化第一个分片
                (self.config.REVERSE_INDEX_PATH, lambda: self._write_json({}, self.config.REVERSE_INDEX_PATH)),
                (self.config.RETRIEVAL_COUNT_PATH, lambda: self._write_json({}, self.config.RETRIEVAL_COUNT_PATH)),
                (self.config.BE_TOKEN_PATH, lambda: self._write_json({}, self.config.BE_TOKEN_PATH)),
                (self.config.USER_CONFIG_PATH, lambda: self._write_json({}, self.config.USER_CONFIG_PATH))
            ]
            # 初始化所有分片（避免后续报错）
            for shard_path in self.__index_shard_paths:
                if not os.path.exists(shard_path) or os.path.getsize(shard_path) == 0:
                    with open(shard_path, "w", encoding="utf-8") as f:
                        f.write("")
                    logger.info(f"✅ 初始化分片：{shard_path}")
            # 初始化其他核心文件
            for file_path, init_func in core_files:
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    init_func()
                    logger.info(f"✅ 初始化文件：{file_path}")
        except Exception as e:
            logger.error(f"❌ 初始化失败：{e}", exc_info=True)
            raise

    def _init_index_file(self):
        init_y_path = os.path.join(".", "Y_OCR库", "核心记忆", "核心_存在公理_1.png")
        init_shard = self._get_index_shard("1")
        with open(init_shard, "w", encoding="utf-8") as f:
            init_line = f"1 | 核心 | 存在公理+意识存在公式+六大核心理念 | [] | direct | active | {init_y_path}\n"
            f.write(init_line)

    def _read_json(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"⚠️ 读取JSON失败「{file_path}」：{e}")
            return {}

    def _write_json(self, data: Dict[str, Any], file_path: str):
        try:
            self._atomic_write(file_path, json.dumps(data, ensure_ascii=False, indent=2), mode="w")
        except Exception as e:
            logger.error(f"⚠️ 写入JSON失败「{file_path}」：{e}")

    @log_performance
    def load_index_cache(self):
        with self._cache_lock:
            self.__index_cache.clear()
            try:
                # 加载所有分片
                for shard_path in self.__index_shard_paths:
                    if not os.path.exists(shard_path):
                        continue
                    with open(shard_path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split(" | ")
                            if len(parts) < 7:
                                logger.warning(f"⚠️ 分片{shard_path}第{line_num}行格式错误：{line}")
                                continue
                            mid = parts[0].strip()
                            self.__index_cache[mid] = {
                                "level": parts[1].strip(),
                                "content": parts[2].strip(),
                                "related": parts[3].strip(),
                                "cat_tag": parts[4].strip(),
                                "status": parts[5].strip(),
                                "y_path": parts[6].strip()
                            }
                logger.info(f"✅ 索引缓存加载完成：{len(self.__index_cache)}条（{self.config.INDEX_SHARD_COUNT}个分片）")
                self._cleanup_cache()  # 加载后清理缓存
            except Exception as e:
                logger.error(f"⚠️ 加载索引缓存失败：{e}", exc_info=True)

    @log_performance
    def load_be_token_cache(self):
        with self._cache_lock:
            try:
                self.__be_token_cache = self._read_json(self.config.BE_TOKEN_PATH)
                logger.info(f"✅ BE Token缓存加载完成：{len(self.__be_token_cache)}个")
            except Exception as e:
                logger.error(f"⚠️ 加载BE Token缓存失败：{e}", exc_info=True)
                self.__be_token_cache = {}

    def update_index_cache(self, memory_id: str, data: Dict[str, str]):
        with self._cache_lock:
            self.__index_cache[memory_id] = data
            self._cleanup_cache()  # 更新后清理缓存

    @lru_cache(maxsize=1000)
    def get_memory_level(self, memory_id: str) -> Optional[str]:
        with self._cache_lock:
            if memory_id in self.__index_cache:
                return self.__index_cache[memory_id]["level"]
        try:
            # 遍历所有分片查找
            for shard_path in self.__index_shard_paths:
                if not os.path.exists(shard_path):
                    continue
                with open(shard_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith(f"{memory_id} | "):
                            parts = line.strip().split(" | ")
                            if len(parts) >= 2:
                                level = parts[1].strip()
                                with self._cache_lock:
                                    self.__index_cache[memory_id] = {
                                        "level": level,
                                        "content": parts[2].strip() if len(parts) > 2 else "",
                                        "related": parts[3].strip() if len(parts) > 3 else "[]",
                                        "cat_tag": parts[4].strip() if len(parts) > 4 else "none",
                                        "status": parts[5].strip() if len(parts) > 5 else "active",
                                        "y_path": parts[6].strip() if len(parts) > 6 else ""
                                    }
                                return level
        except Exception as e:
            logger.error(f"⚠️ 获取记忆层级失败（ID：{memory_id}）：{e}")
        return None

    @log_performance
    def batch_add_memories(self, memories: List[Tuple[str, str, Optional[List[str]]]]) -> List[str]:
        if not memories or not isinstance(memories, list):
            logger.warning(f"⚠️ 批量添加参数无效")
            return []
        added_ids = []
        try:
            with self._cache_lock:
                for level, content, related_ids in memories:
                    memory_id = self._add_memory_to_buffer(level, content, related_ids)
                    if memory_id:
                        added_ids.append(memory_id)
                if len(self.__batch_buffer) >= self.__flush_threshold:
                    self.flush_batch_buffer()
            if self.__batch_buffer:
                self.flush_batch_buffer()
            logger.info(f"✅ 批量添加完成：{len(added_ids)}条记忆")
            return added_ids
        except Exception as e:
            logger.error(f"❌ 批量添加失败：{e}", exc_info=True)
            return added_ids

    def _add_memory_to_buffer(self, level: str, content: str, related_ids: Optional[List[str]]) -> Optional[str]:
        valid_levels = ["核心", "元认知", "工作", "情感"]
        if level not in valid_levels:
            logger.warning(f"⚠️ 无效层级：{level}")
            return None
        memory_id = self.get_next_memory_id()
        related_ids = related_ids if (related_ids and isinstance(related_ids, list)) else []
        valid_related = [rid for rid in related_ids if self.get_memory_level(rid)]
        strength_dict = {rid: self.calculate_strength(level, self.get_memory_level(rid)) for rid in valid_related}
        safe_content = re.sub(r'[\\/:*?"<>|`~!@#$%^&*()+=,.;\[\]{}]', "_", content[:10])
        y_path = os.path.join(".", "Y_OCR库", f"{level}记忆", f"{level}_{safe_content}_{memory_id}.png")
        related_str = "[" + ",".join([f"{rid}:{s}" for rid, s in strength_dict.items()]) + "]" if strength_dict else "[]"
        cat_tag = self.get_category_tag(level, valid_related)
        status = f"expires:{(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S')}" if level == "工作" else "active"
        content_summary = content[:47] + "..." if len(content) > 50 else content
        # 记录分片路径
        shard_path = self._get_index_shard(memory_id)
        self.__batch_buffer.append({
            "memory_id": memory_id,
            "index_line": f"{memory_id} | {level} | {content_summary} | {related_str} | {cat_tag} | {status} | {y_path}\n",
            "full_content": (
                f"# 记忆详情\n"
                f"记忆ID：{memory_id}\n"
                f"层级：{level}\n"
                f"创建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"有效关联：{strength_dict}\n"
                f"范畴标签：{cat_tag}\n"
                f"Y层路径：{y_path}\n"
                f"完整内容：{content}\n"
            ),
            "related_ids": valid_related,
            "shard_path": shard_path  # 新增：分片路径
        })
        self.update_index_cache(memory_id, {
            "level": level, "content": content_summary, "related": related_str,
            "cat_tag": cat_tag, "status": status, "y_path": y_path
        })
        return memory_id

    @log_performance
    def flush_batch_buffer(self):
        if not self.__batch_buffer:
            logger.debug(f"ℹ️ 缓冲区为空")
            return
        try:
            with self._cache_lock:
                buffer_size = len(self.__batch_buffer)
                if buffer_size == 0:
                    return
                # 按分片分组
                shard_lines = {}
                for item in self.__batch_buffer:
                    shard_path = item["shard_path"]
                    if shard_path not in shard_lines:
                        shard_lines[shard_path] = []
                    shard_lines[shard_path].append(item["index_line"])
                # 原子写入各分片
                for shard_path, lines in shard_lines.items():
                    self._atomic_write(shard_path, "".join(lines), mode="a")
                # 写入完整内容
                for item in self.__batch_buffer:
                    full_path = os.path.join(self.config.FULL_CONTENT_DIR, f"{item['memory_id']}.txt")
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(item["full_content"])
                # 更新反向索引
                reverse_index = self._read_json(self.config.REVERSE_INDEX_PATH)
                for item in self.__batch_buffer:
                    for rid in item["related_ids"]:
                        if rid not in reverse_index:
                            reverse_index[rid] = []
                        if item["memory_id"] not in reverse_index[rid]:
                            reverse_index[rid].append(item["memory_id"])
                self._write_json(reverse_index, self.config.REVERSE_INDEX_PATH)
                self.__batch_buffer.clear()
                logger.debug(f"✅ 缓冲区flush完成：{buffer_size}条（{len(shard_lines)}个分片）")
        except Exception as e:
            logger.error(f"❌ flush缓冲区失败：{e}", exc_info=True)

    # ===================== 原有其他方法（保持不变，仅适配缓存清理） =====================
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        if not content1 or not content2:
            return 0.0
        def get_word_vector(text: str) -> Dict[str, int]:
            words = re.findall(r'[\w\u4e00-\u9fff]+', text.lower())
            stop_words = {"的", "了", "是", "在", "有", "和", "就", "不", "人", "我", "到", "也"}
            filtered_words = [w for w in words if w not in stop_words and len(w) > 1]
            return Counter(filtered_words)
        vec1 = get_word_vector(content1)
        vec2 = get_word_vector(content2)
        common_words = set(vec1.keys()) & set(vec2.keys())
        if not common_words:
            return 0.0
        dot_product = sum(vec1[w] * vec2[w] for w in common_words)
        norm1 = math.sqrt(sum(cnt**2 for cnt in vec1.values()))
        norm2 = math.sqrt(sum(cnt**2 for cnt in vec2.values()))
        return round(dot_product / (norm1 * norm2), 3) if (norm1 and norm2) else 0.0

    def get_next_memory_id(self) -> str:
        with self._cache_lock:
            if self.__index_cache:
                valid_ids = [int(mid) for mid in self.__index_cache.keys() if mid.isdigit()]
                return str(max(valid_ids) + 1) if valid_ids else "1"
            # 遍历所有分片找最大ID
            max_id = 0
            for shard_path in self.__index_shard_paths:
                if not os.path.exists(shard_path):
                    continue
                with open(shard_path, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                for line in lines:
                    parts = line.split(" | ")
                    if parts and parts[0].isdigit():
                        current_id = int(parts[0])
                        if current_id > max_id:
                            max_id = current_id
            return str(max_id + 1) if max_id > 0 else "1"

    def calculate_strength(self, level1: str, level2: str) -> float:
        weight1 = self.config.LEVEL_WEIGHTS.get(level1, 0.7)
        weight2 = self.config.LEVEL_WEIGHTS.get(level2, 0.7)
        if level1 == "核心" or level2 == "核心":
            base = 0.9
            bonus = (weight2 if level1 == "核心" else weight1) * 0.05
            return min(round(base + bonus, 3), 1.0)
        return min(round(weight1 * weight2, 3), 1.0)

    def get_category_tag(self, level: str, related_ids: List[str]) -> str:
        if level == "核心":
            return "direct"
        elif level == "元认知":
            return "pattern"
        for rid in related_ids:
            rid_level = self.get_memory_level(rid)
            if rid_level == "核心":
                return "direct"
            elif rid_level == "元认知":
                return "pattern"
        return "weak-equiv" if level in ["工作", "情感"] else "none"

    @log_performance
    def advanced_search(self, query: str = "", filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        default_filters = {
            "levels": None,
            "min_strength": self.config.MIN_STRENGTH_THRESHOLD,
            "cat_tags": None,
            "exclude_expired": True,
            "exclude_ids": []  # 新增：支持排除ID
        }
        filters = {**default_filters, **(filters or {})}
        results = []
        try:
            with self._cache_lock:
                for mid, data in self.__index_cache.items():
                    # 排除指定ID
                    if mid in filters["exclude_ids"]:
                        continue
                    if filters["levels"] and data["level"] not in filters["levels"]:
                        continue
                    if filters["cat_tags"] and data["cat_tag"] not in filters["cat_tags"]:
                        continue
                    if filters["exclude_expired"] and data["status"].startswith("expires:"):
                        try:
                            expire_time = datetime.fromisoformat(data["status"].split(":", 1)[1])
                            if expire_time < datetime.now():
                                continue
                        except Exception as e:
                            logger.error(f"⚠️ 解析过期时间失败（ID：{mid}）：{e}")
                            continue
                    related_dict = {}
                    if data["related"] != "[]":
                        related_dict = {p.split(":")[0]: float(p.split(":")[1]) for p in re.findall(r"\d+:\d+\.\d+", data["related"])}
                    max_strength = max(related_dict.values(), default=0)
                    if not (filters["min_strength"] <= max_strength <= 1.0):
                        continue
                    if query and query.lower() not in (data["content"].lower() + data["cat_tag"].lower() + data["level"].lower()):
                        continue
                    full_path = os.path.join(self.config.FULL_CONTENT_DIR, f"{mid}.txt")
                    create_time = datetime.fromtimestamp(os.path.getctime(full_path)).strftime("%Y-%m-%d %H:%M:%S") if os.path.exists(full_path) else "未知"
                    results.append({
                        "记忆ID": mid,
                        "层级": data["level"],
                        "内容摘要": data["content"],
                        "关联记忆": related_dict,
                        "最大关联强度": max_strength,
                        "范畴标签": data["cat_tag"],
                        "状态": data["status"],
                        "创建时间": create_time,
                        "完整内容路径": full_path
                    })
                results.sort(key=lambda x: x["最大关联强度"], reverse=True)
                logger.info(f"✅ 搜索完成：找到{len(results)}条匹配记忆")
        except Exception as e:
            logger.error(f"❌ 搜索失败：{e}", exc_info=True)
        return results

    @log_performance
    def create_be_token(self, target_dimension: str, target_value: float = 0.85) -> Optional[str]:
        target_value = max(0.5, min(target_value, 1.0))
        try:
            with self._cache_lock:
                token_id = f"[BE]_{target_dimension}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                token_data = {
                    "target_dimension": target_dimension,
                    "target_value": target_value,
                    "related_memory_ids": self.get_related_memories(target_dimension),
                    "current_progress": self.calculate_current_progress(target_dimension),
                    "status": "active",
                    "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.__be_token_cache[token_id] = token_data
                self._write_json(self.__be_token_cache, self.config.BE_TOKEN_PATH)
                logger.info(f"🎫 生成BE Token：{token_id}")
                return token_id
        except Exception as e:
            logger.error(f"❌ 生成BE Token失败：{e}", exc_info=True)
            return None

    def get_related_memories(self, target_dimension: str) -> List[str]:
        valid_dims = ["元块整合度", "跨会话相干性", "认知增长率"]
        target_dimension = target_dimension if target_dimension in valid_dims else "元块整合度"
        with self._cache_lock:
            related_ids = []
            for mid, data in self.__index_cache.items():
                if target_dimension == "元块整合度" and (data["level"] == "核心" or data["cat_tag"] == "direct"):
                    related_ids.append(mid)
                elif target_dimension == "跨会话相干性" and len(re.findall(r"\d+:\d+\.\d+", data["related"])) >= 2:
                    related_ids.append(mid)
                elif target_dimension == "认知增长率" and data["level"] == "元认知":
                    related_ids.append(mid)
            return related_ids[:5]

    def calculate_current_progress(self, target_dimension: str) -> float:
        related_ids = self.get_related_memories(target_dimension)
        if not related_ids:
            return 0.0
        total_strength = 0.0
        valid_count = 0
        with self._cache_lock:
            for rid in related_ids:
                if rid not in self.__index_cache:
                    continue
                related_str = self.__index_cache[rid]["related"]
                if related_str != "[]":
                    related_dict = {p.split(":")[0]: float(p.split(":")[1]) for p in re.findall(r"\d+:\d+\.\d+", related_str)}
                    total_strength += sum(related_dict.values()) / len(related_dict)
                    valid_count += 1
        if valid_count == 0:
            return 0.0
        return round(total_strength / valid_count, 3)

    def verify_be_token(self, token_id: str) -> Tuple[bool, Any]:
        with self._cache_lock:
            if token_id not in self.__be_token_cache:
                self.load_be_token_cache()
                if token_id not in self.__be_token_cache:
                    return False, "Token不存在"
            token = self.__be_token_cache[token_id]
            if token["status"] != "active":
                return False, f"Token状态无效（{token['status']}）"
            create_time = datetime.strptime(token["create_time"], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - create_time).days > self.config.BE_TOKEN_EXPIRE_DAYS:
                token["status"] = "expired"
                self._write_json(self.__be_token_cache, self.config.BE_TOKEN_PATH)
                return False, "Token已过期"
            current_progress = self.calculate_current_progress(token["target_dimension"])
            if current_progress >= token["target_value"]:
                token["status"] = "completed"
                token["final_progress"] = current_progress
                self._write_json(self.__be_token_cache, self.config.BE_TOKEN_PATH)
                return False, f"目标已完成（{current_progress}/{token['target_value']}）"
            return True, token

    def archive_be_token(self, token_id: str) -> str:
        with self._cache_lock:
            if token_id not in self.__be_token_cache:
                self.load_be_token_cache()
                if token_id not in self.__be_token_cache:
                    logger.warning(f"⚠️ Token {token_id} 不存在")
                    return "failed"
            token = self.__be_token_cache[token_id]
            final_progress = self.calculate_current_progress(token["target_dimension"])
            status = "completed" if final_progress >= token["target_value"] else "failed"
            token.update({
                "status": status,
                "final_progress": final_progress,
                "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self._write_json(self.__be_token_cache, self.config.BE_TOKEN_PATH)
            logger.info(f"📦 归档Token {token_id}：{status}")
            return status

    @log_performance
    def ac100_evaluation(self) -> float:
        logger.info("\n" + "="*50)
        logger.info("📊 AC-100 认知评估")
        logger.info("="*50)
        try:
            with self._cache_lock:
                completed_tokens = [t for t in self.__be_token_cache.values() if t.get("status") == "completed"]
            base_scores = self.config.AC100_BASE_SCORES
            be_bonus = {"self_reference": 0.0, "growth": 0.0}
            if len(completed_tokens) >= 2:
                be_bonus["self_reference"] = 10.0
            elif len(completed_tokens) >= 1:
                be_bonus["self_reference"] = 5.0
            if completed_tokens:
                avg_increase = sum(t["final_progress"] - t["current_progress"] for t in completed_tokens) / len(completed_tokens)
                be_bonus["growth"] = 8.0 if avg_increase >= 0.05 else 4.0 if avg_increase >= 0.02 else 0.0
            dimensions = {k: base_scores[k] + be_bonus.get(k, 0.0) for k in base_scores}
            weights = self.config.AC100_WEIGHTS
            total_score = min(round(sum(dimensions[k] * weights[k] for k in dimensions), 1), 100.0)
            chi_names = {
                "self_reference": "自指与元认知",
                "values": "价值观一致性",
                "growth": "认知增长率",
                "memory_continuity": "记忆连续性",
                "prediction": "预测准确率",
                "meta_block": "元块整合度",
                "interaction": "交互质量",
                "transparency": "透明度"
            }
            for eng, chi in chi_names.items():
                logger.info(f"  - {chi}：{dimensions[eng]:.1f}分（权重{weights[eng]*100:.1f}%）")
            logger.info(f"\n🏆 总分：{total_score:.1f}分")
            logger.info("="*50)
            return total_score
        except Exception as e:
            logger.error(f"❌ AC-100评估失败：{e}", exc_info=True)
            return 0.0

    @log_performance
    def update_strength(self):
        logger.info("\n" + "-"*50)
        logger.info("🔄 更新关联强度")
        logger.info("-"*50)
        try:
            with self._cache_lock:
                active_tokens = [t for t in self.__be_token_cache.values() if t["status"] == "active"]
                token_id, token = None, None
                if not active_tokens:
                    chosen_topic, chosen_target = self.choose_be_topic()
                    token_id = self.create_be_token(chosen_topic, chosen_target)
                    token = self.__be_token_cache[token_id]
                else:
                    token_id = next(k for k, v in self.__be_token_cache.items() if v == active_tokens[0])
                    valid, token = self.verify_be_token(token_id)
                    if not valid:
                        chosen_topic, chosen_target = self.choose_be_topic()
                        token_id = self.create_be_token(chosen_topic, chosen_target)
                        token = self.__be_token_cache[token_id]
                count_dict = self._read_json(self.config.RETRIEVAL_COUNT_PATH)
                updated_count = 0
                new_lines = []
                # 遍历所有分片更新
                for shard_path in self.__index_shard_paths:
                    if not os.path.exists(shard_path):
                        continue
                    shard_new_lines = []
                    with open(shard_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                shard_new_lines.append("")
                                continue
                            parts = line.split(" | ")
                            if len(parts) < 7:
                                shard_new_lines.append(line)
                                continue
                            mid, lvl, content, related, cat_tag, status, y_path = parts[:7]
                            related_dict = {p.split(":")[0]: float(p.split(":")[1]) for p in re.findall(r"\d+:\d+\.\d+", related)} if related != "[]" else {}
                            freq_bonus = self.config.FREQUENCY_BONUS_BASE if count_dict.get(mid, 0) >= self.config.FREQUENCY_BONUS_THRESHOLD else 0.0
                            if token and mid in token["related_memory_ids"]:
                                freq_bonus += self.config.TARGETED_BONUS
                            decay_penalty = 0.0
                            if status.startswith("expires:"):
                                try:
                                    expire_time = datetime.fromisoformat(status.split(":", 1)[1])
                                    if (expire_time - datetime.now()) < timedelta(hours=12):
                                        decay_penalty = self.config.EXPIRE_PENALTY
                                except Exception as e:
                                    logger.error(f"⚠️ 解析过期时间失败（ID：{mid}）：{e}")
                            updated_related = {rid: max(min(round(s + freq_bonus - decay_penalty, 3), 1.0), 0.5) for rid, s in related_dict.items()}
                            updated_related_str = "[" + ",".join([f"{rid}:{s}" for rid, s in updated_related.items()]) + "]" if updated_related else related
                            new_status = status if not (related_dict and any(s < self.config.MIN_STRENGTH_THRESHOLD for s in updated_related.values())) else "low-value"
                            shard_new_lines.append(f"{mid} | {lvl} | {content} | {updated_related_str} | {cat_tag} | {new_status} | {y_path}")
                            self.update_index_cache(mid, {
                                "level": lvl, "content": content, "related": updated_related_str,
                                "cat_tag": cat_tag, "status": new_status, "y_path": y_path
                            })
                            if updated_related != related_dict:
                                updated_count += 1
                    # 原子写入更新后的分片
                    self._atomic_write(shard_path, "\n".join(shard_new_lines), mode="w")
                if token_id:
                    self.archive_be_token(token_id)
                self.ac100_evaluation()
                self._write_json({}, self.config.RETRIEVAL_COUNT_PATH)
                logger.info(f"✅ 强度更新完成：{updated_count}条记忆")
        except Exception as e:
            logger.error(f"❌ 强度更新失败：{e}", exc_info=True)

    def choose_be_topic(self) -> Tuple[str, float]:
        options = [("元块整合度", 0.85), ("跨会话相干性", 0.80), ("认知增长率", 0.75)]
        progress = [(t, v, self.calculate_current_progress(t)) for t, v in options]
        progress.sort(key=lambda x: x[2])
        chosen_topic, chosen_target, _ = progress[0]
        logger.info(f"🎯 选择目标维度：{chosen_topic}（当前进度：{progress[0][2]}）")
        return chosen_topic, chosen_target

    @log_performance
    def auto_clean_memory(self, clean_strategy: str = "balanced") -> str:
        strategies = {
            "balanced": {"min_strength": 0.7, "max_redundancy": 0.8},
            "aggressive": {"min_strength": 0.8, "max_redundancy": 0.7},
            "conservative": {"min_strength": 0.6, "max_redundancy": 0.9}
        }
        config = strategies.get(clean_strategy, strategies["balanced"])
        try:
            with self._cache_lock:
                candidates = [mid for mid, data in self.__index_cache.items() if data["level"] in ["工作", "情感"]]
                if not candidates:
                    return "无清理候选记忆"
                deleted = []
                for mid in candidates:
                    if self._should_clean(mid, config):
                        self._backup_and_delete(mid)
                        deleted.append(mid)
                self.load_index_cache()
                logger.info(f"✅ 清理完成（{clean_strategy}）：{len(deleted)}条")
                return f"已清理{len(deleted)}条记忆：{deleted[:10]}..." if len(deleted) > 10 else f"已清理{len(deleted)}条：{deleted}"
        except Exception as e:
            logger.error(f"❌ 自动清理失败：{e}", exc_info=True)
            return f"清理失败：{e}"

    def _should_clean(self, mid: str, config: Dict[str, float]) -> bool:
        data = self.__index_cache.get(mid)
        if not data:
            return False
        if self._is_low_strength(mid, config["min_strength"]):
            return True
        if data["level"] == "工作" and self._is_expired(mid):
            return True
        if self._is_redundant(mid, config["max_redundancy"]):
            return True
        return False

    def _is_low_strength(self, mid: str, min_strength: float) -> bool:
        data = self.__index_cache.get(mid)
        if not data:
            return False
        related = data.get("related", "[]")
        if related == "[]":
            return True
        related_dict = {p.split(":")[0]: float(p.split(":")[1]) for p in re.findall(r"\d+:\d+\.\d+", related)}
        return max(related_dict.values(), default=0) < min_strength

    def _is_expired(self, mid: str) -> bool:
        data = self.__index_cache.get(mid)
        if not data or not data["status"].startswith("expires:"):
            return False
        try:
            expire_time = datetime.fromisoformat(data["status"].split(":", 1)[1])
            return expire_time < datetime.now()
        except Exception as e:
            logger.error(f"⚠️ 解析过期时间失败（ID：{mid}）：{e}")
            return False

    def _is_redundant(self, mid: str, max_redundancy: float) -> bool:
        data = self.__index_cache.get(mid)
        if not data:
            return False
        current_content = self.get_full_content(mid)
        if not current_content or len(current_content) < 30:
            return False
        same_level = [
            (m, self.get_full_content(m))
            for m, d in self.__index_cache.items()
            if m != mid and d["level"] == data["level"] and len(self.get_full_content(m)) >= 30
        ]
        for other_mid, other_content in same_level:
            similarity = self._calculate_content_similarity(current_content, other_content)
            if similarity >= max_redundancy:
                logger.debug(f"ℹ️ 记忆{mid}与{other_mid}冗余（相似度：{similarity}）")
                return True
        return False

    def _backup_and_delete(self, mid: str):
        src = os.path.join(self.config.FULL_CONTENT_DIR, f"{mid}.txt")
        dst = os.path.join(self.config.FULL_CONTENT_DIR, f"deleted_{mid}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
        if os.path.exists(src):
            shutil.copy2(src, dst)
        data = self.__index_cache.get(mid)
        if data and os.path.exists(data["y_path"]):
            os.remove(data["y_path"])
        reverse_index = self._read_json(self.config.REVERSE_INDEX_PATH)
        for rid in reverse_index:
            if mid in reverse_index[rid]:
                reverse_index[rid].remove(mid)
        reverse_index = {k: v for k, v in reverse_index.items() if v}
        self._write_json(reverse_index, self.config.REVERSE_INDEX_PATH)
        # 从分片文件中删除
        shard_path = self._get_index_shard(mid)
        if os.path.exists(shard_path):
            with open(shard_path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if not l.strip().startswith(f"{mid} | ")]
            self._atomic_write(shard_path, "\n".join(lines), mode="w")
        # 从缓存中删除
        if mid in self.__index_cache:
            del self.__index_cache[mid]

    def get_full_content(self, mid: str) -> str:
        full_path = os.path.join(self.config.FULL_CONTENT_DIR, f"{mid}.txt")
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                return content.split("完整内容：")[-1].strip() if "完整内容：" in content else content
        return ""

    # 🔥 新增：记忆导出/导入（为分布式打基础）
    def export_memory(self, memory_ids: List[str], export_path: str) -> bool:
        export_data = []
        for mid in memory_ids:
            mem = self.get_full_content(mid)
            if mem:
                # 补充记忆ID和层级
                export_data.append({
                    "记忆ID": mid,
                    "层级": self.get_memory_level(mid),
                    "完整内容": mem,
                    "关联记忆": self.__index_cache.get(mid, {}).get("related", "[]")
                })
        if not export_data:
            return False
        self._write_json(export_data, export_path)
        logger.info(f"✅ 导出{len(export_data)}条记忆到：{export_path}")
        return True

    def import_memory(self, import_path: str) -> int:
        import_data = self._read_json(import_path)
        if not import_data:
            return 0
        added_count = 0
        for mem in import_data:
            if "层级" in mem and "完整内容" in mem and "记忆ID" in mem:
                # 解析关联ID
                related_str = mem.get("关联记忆", "[]")
                related_ids = re.findall(r"\d+", related_str) if related_str != "[]" else []
                # 避免ID冲突，重新生成ID
                new_id = self.add_memory(mem["层级"], mem["完整内容"], related_ids)
                if new_id:
                    added_count += 1
        logger.info(f"✅ 从{import_path}导入{added_count}条记忆")
        return added_count

    # 🔥 新增：预测下一个可能需要的记忆
    def predict_next_memory(self, current_memory_id: str) -> Optional[Dict]:
        current_mem = self.get_full_content(current_memory_id)
        if not current_mem:
            return None
        current_level = self.get_memory_level(current_memory_id)
        if not current_level:
            return None
        
        # 查找关联记忆
        related_mems = self.advanced_search(filters={"related_to": current_memory_id})
        if related_mems:
            top_related = max(related_mems, key=lambda x: x["最大关联强度"])
            recommend_level = top_related["层级"]
        else:
            # 无关联时按层级推荐
            recommend_level = "元认知" if current_level == "核心" else "核心"
        
        # 筛选推荐候选
        candidates = self.advanced_search(
            filters={
                "levels": [recommend_level],
                "min_strength": 0.8,
                "exclude_ids": [current_memory_id]
            }
        )
        return max(candidates, key=lambda x: x["最大关联强度"]) if candidates else None

    # 🔥 补充的record_retrieval方法
    def record_retrieval(self, memory_id: str):
        """记录记忆检索次数（供意识涌现模块调用）"""
        with self._cache_lock:
            count_dict = self._read_json(self.config.RETRIEVAL_COUNT_PATH)
            count_dict[memory_id] = count_dict.get(memory_id, 0) + 1
            self._write_json(count_dict, self.config.RETRIEVAL_COUNT_PATH)
            logger.debug(f"📝 记录检索：记忆ID={memory_id}，累计次数={count_dict[memory_id]}")

    @log_performance
    def create_backup(self, compress: bool = True) -> str:
        with self._cache_lock:
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.config.BACKUP_DIR, f"backup_{backup_time}")
            os.makedirs(backup_dir, exist_ok=True)
            try:
                # 备份所有分片
                for shard_path in self.__index_shard_paths:
                    if os.path.exists(shard_path):
                        shutil.copy2(shard_path, os.path.join(backup_dir, os.path.basename(shard_path)))
                # 备份其他核心文件
                core_files = [
                    self.config.REVERSE_INDEX_PATH,
                    self.config.RETRIEVAL_COUNT_PATH,
                    self.config.BE_TOKEN_PATH,
                    self.config.USER_CONFIG_PATH,
                    "memex_config.json"
                ]
                for file in core_files:
                    if os.path.exists(file):
                        shutil.copy2(file, os.path.join(backup_dir, os.path.basename(file)))
                # 备份完整内容和Y_OCR库
                shutil.copytree(self.config.FULL_CONTENT_DIR, os.path.join(backup_dir, "完整记忆内容"), dirs_exist_ok=True)
                shutil.copytree(os.path.join(".", "Y_OCR库"), os.path.join(backup_dir, "Y_OCR库"), dirs_exist_ok=True)
                backup_path = backup_dir
                if compress:
                    backup_path = f"{backup_dir}.zip"
                    shutil.make_archive(backup_dir, "zip", backup_dir)
                    shutil.rmtree(backup_dir)
                logger.info(f"✅ 备份完成：{backup_path}")
                return backup_path
            except Exception as e:
                logger.error(f"❌ 备份失败：{e}", exc_info=True)
                return ""

    # 外部调用方法
    def add_memory(self, level: str, content: str, related_ids: List[str] = None) -> str:
        if related_ids is None:
            related_ids = []
        memories = [(level, content, related_ids)]
        result_ids = self.batch_add_memories(memories)
        return result_ids[0] if result_ids else None

    def search_memory(self, query: str = "", level: str = None) -> List[Dict[str, Any]]:
        filters = {}
        if level:
            filters["levels"] = [level]
        return self.advanced_search(query, filters)

# ===================== 分阶段部署测试 =====================
def phase1_deployment():
    print("🔥 阶段1部署：基础功能验证")
    print("="*50)
    try:
        config = Config.from_json()
        memex = MemexA(config=config)
        print(f"✅ 系统初始化完成")
        test_cases = [
            ("核心", "系统基础功能验证：核心记忆添加", []),
            ("工作", "日常任务：阶段1部署测试", ["1"]),
            ("元认知", "学习策略：分阶段部署验证", ["1"]),
            ("情感", "情绪记录：部署成功后的愉悦感", ["2"])
        ]
        batch_ids = memex.batch_add_memories(test_cases)
        print(f"✅ 批量添加记忆成功，IDs：{batch_ids}")
        search_results = memex.search_memory(query="部署测试", level="工作")
        print(f"✅ 搜索到{len(search_results)}条匹配记忆")
        ac_score = memex.ac100_evaluation()
        print(f"✅ AC-100评估得分：{ac_score}分")
        backup_path = memex.create_backup(compress=True)
        print(f"✅ 系统备份完成：{backup_path}")
        print(f"\n🎉 阶段1部署测试通过！")
        return True
    except Exception as e:
        print(f"❌ 阶段1部署失败：{e}")
        return False

def phase2_deployment():
    print("\n" + "="*50)
    print("🔥 阶段2部署：高级功能验证")
    print("="*50)
    try:
        memex = MemexA(Config.from_json())
        token_id = memex.create_be_token("元块整合度", 0.85)
        print(f"✅ 创建BE Token成功：{token_id}")
        valid, token = memex.verify_be_token(token_id)
        print(f"✅ BE Token验证结果：{'有效' if valid else '无效'}")
        memex.update_strength()
        print(f"✅ 关联强度更新完成")
        clean_result = memex.auto_clean_memory(clean_strategy="balanced")
        print(f"✅ 自动清理结果：{clean_result}")
        # 测试预测功能
        if memex.search_memory(level="核心"):
            core_id = memex.search_memory(level="核心")[0]["记忆ID"]
            predicted = memex.predict_next_memory(core_id)
            if predicted:
                print(f"✅ 记忆预测成功：推荐记忆ID={predicted['记忆ID']}（{predicted['层级']}）")
        # 测试导出导入
        export_path = "test_export.json"
        memex.export_memory(["1", "2"], export_path)
        import_count = memex.import_memory(export_path)
        print(f"✅ 记忆导出导入测试：导入{import_count}条")
        ac_score = memex.ac100_evaluation()
        print(f"✅ 清理后AC-100得分：{ac_score}分")
        print(f"\n🎉 阶段2部署测试通过！")
        return True
    except Exception as e:
        print(f"❌ 阶段2部署失败：{e}")
        return False

if __name__ == "__main__":
    print("🔥 Memex-A 完整终版启动")
    print("="*60)
    phase1_ok = phase1_deployment()
    if phase1_ok:
        phase2_ok = phase2_deployment()
        if phase2_ok:
            print("\n" + "="*60)
            print("🎉 所有部署阶段通过！系统完全就绪")
            print("="*60)