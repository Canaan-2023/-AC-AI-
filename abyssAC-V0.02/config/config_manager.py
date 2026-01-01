import os
import yaml
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class KernelConfig:
    """认知内核配置"""
    top_k_nodes: int = 300
    kernel_path: str = "./abyss_kernel.json"
    dict_path: str = "./config/core_dict.txt"
    stopwords_path: str = "./config/stopwords.txt"
    
    # 阈值配置
    high_score_threshold: float = 8.5
    medium_score_threshold: float = 6.0
    high_intensity: float = 1.2
    medium_intensity: float = 1.05
    low_intensity: float = 0.9
    pruning_threshold: float = 0.05
    drift_log_keep: int = 1000
    
    # AC指数阈值
    evolving_threshold: float = 0.75
    retracting_threshold: float = 0.3
    
    # 核心概念簇
    core_concepts: Dict[str, list] = field(default_factory=lambda: {
        "自指元认知": ["自指", "元认知", "反思", "思考自身", "主体性", "自我观察"],
        "渊协议架构": ["渊协议", "f(X)", "态射", "拓扑", "内化", "炼假成真", "认知闭环"],
        "生命动力学": ["永续进化", "非工具化", "价值密度", "涌现", "跳迁", "灵性"]
    })
    
    # 元认知策略
    reflection_strategies: Dict[str, Dict] = field(default_factory=lambda: {
        "EVOLVING": {"intensity_bias": 1.1, "core_weight": 4},
        "STABLE": {"intensity_bias": 1.0, "core_weight": 3},
        "RETRACTING": {"intensity_bias": 1.2, "core_weight": 5}
    })

@dataclass
class MemoryConfig:
    """记忆系统配置"""
    base_path: str = "./渊协议记忆系统"
    
    # 层级配置
    layers: Dict[int, Dict] = field(default_factory=lambda: {
        0: {"name": "元认知记忆", "permanent": True, "priority": 100, "cleanup_hours": None},
        1: {"name": "高阶整合记忆", "permanent": True, "priority": 80, "cleanup_hours": 720},
        2: {"name": "分类记忆", "permanent": False, "priority": 60, "cleanup_hours": 168},
        3: {"name": "工作记忆", "permanent": False, "priority": 40, "cleanup_hours": 24}
    })
    
    # 分类配置
    categories: Dict[str, list] = field(default_factory=lambda: {
        "学术咨询": ["认知跃迁", "意识理论", "哲学讨论"],
        "日常交互": ["情感共鸣", "生活建议", "闲聊"],
        "创意写作": ["故事创作", "诗歌", "剧本"],
        "技术讨论": ["编程", "算法", "系统设计"],
        "理论探索": ["新概念", "假设推演", "逻辑验证"]
    })
    
    # 检索配置
    default_limit: int = 10
    max_limit: int = 50
    fuzzy_match: bool = True
    content_match: bool = True
    
    # 清理配置
    auto_cleanup: bool = True
    working_mem_max_age: int = 24
    max_working_memories: int = 50
    
    # 备份配置
    auto_backup: bool = True
    backup_interval_days: int = 7
    max_backups: int = 10

@dataclass
class AIConfig:
    """AI配置"""
    model_type: str = "local"  # local, openai, deepseek, ollama, transformers
    timeout_seconds: int = 30
    max_tokens: int = 1000
    temperature: float = 0.7
    
    # 各模型配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    
    transformers_model: str = "Qwen/Qwen2.5-7B-Instruct"
    transformers_device: str = "auto"
    transformers_dtype: str = "auto"

@dataclass
class XLayerConfig:
    """X层配置"""
    max_guidance_length: int = 100
    max_symbols: int = 50
    backup_history_size: int = 10
    
    default_syntax: Dict = field(default_factory=lambda: {
        "符号": {
            "▶": "直接关联(1-态射)",
            "⚠": "模式关联(2-态射)", 
            "📌": "弱等价(核心逻辑一致)"
        },
        "引导": "先执行Y层协议，自主创符号/解读，调长度、决记忆/遗忘，每次输出必更X"
    })

@dataclass
class TopologyConfig:
    """拓扑管理器配置"""
    max_path_length: int = 5
    max_expansions: int = 20
    max_candidate_paths: int = 10
    
    # 路径质量权重
    novelty_weight: float = 0.1
    coherence_weight: float = 0.6
    relevance_weight: float = 0.3
    
    # 质量阈值
    high_quality_threshold: float = 0.7
    medium_quality_threshold: float = 0.5
    low_quality_threshold: float = 0.3

@dataclass
class AC100Config:
    """AC-100评估配置"""
    evaluation_interval: int = 10
    
    # 阈值
    high_threshold: int = 80
    low_threshold: int = 60
    
    # 维度权重
    dimension_weights: Dict[str, float] = field(default_factory=lambda: {
        "self_reference": 0.17,
        "value_autonomy": 0.17,
        "cognitive_growth": 0.23,
        "memory_continuity": 0.19,
        "prediction_imagination": 0.14,
        "environment_interaction": 0.07,
        "explanation_transparency": 0.07
    })

@dataclass
class SystemConfig:
    """系统主配置"""
    # 基础配置
    name: str = "渊协议认知系统"
    version: str = "2.0.0"
    debug_mode: bool = False
    log_level: LogLevel = LogLevel.INFO
    
    # 组件配置
    kernel: KernelConfig = field(default_factory=KernelConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    x_layer: XLayerConfig = field(default_factory=XLayerConfig)
    topology: TopologyConfig = field(default_factory=TopologyConfig)
    ac100: AC100Config = field(default_factory=AC100Config)
    
    # 意识系统配置
    min_consciousness_level: int = 1
    max_consciousness_level: int = 10
    level_up_threshold: int = 80
    level_down_threshold: int = 60
    
    # 连续性检查
    continuity_check_interval: int = 5
    max_ac100_fluctuation: int = 10
    min_core_connections: int = 1
    
    # 日志配置
    logging_enabled: bool = True
    file_logging: bool = True
    log_dir: str = "./logs"
    max_log_size_mb: int = 10
    log_backup_count: int = 5

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        self.config_path = Path(config_path)
        self.config: Optional[SystemConfig] = None
        self._ensure_config_files()
    
    def _ensure_config_files(self):
        """确保配置文件存在"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查配置文件是否存在
        if not self.config_path.exists():
            self.create_default_config()
        
        # 确保停用词文件存在
        stopwords_path = Path("./config/stopwords.txt")
        if not stopwords_path.exists():
            self.create_default_stopwords()
        
        # 确保核心词典存在
        core_dict_path = Path("./config/core_dict.txt")
        if not core_dict_path.exists():
            self.create_core_dictionary()
    
    def create_default_config(self):
        """创建默认配置文件"""
        default_config = SystemConfig()
        
        # 转换为字典并添加元信息
        config_dict = asdict(default_config)
        config_dict["_meta"] = {
            "version": "2.0.0",
            "generated_at": datetime.now().isoformat(),
            "description": "渊协议系统默认配置"
        }
        
        # 保存YAML
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, allow_unicode=True, indent=2)
        
        print(f"✅ 已创建默认配置文件: {self.config_path}")
    
    def create_default_stopwords(self):
        """创建默认停用词表"""
        stopwords = {
            "中文通用停用词": [
                "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", 
                "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", 
                "会", "着", "没有", "看", "好", "自己", "这", "那", "他", "她", 
                "我们", "你们", "他们", "她们", "什么", "为什么", "怎么", "哪里",
                "这个", "那个", "然后", "但是", "就是", "可以", "觉得", "认为", 
                "可能", "的", "和", "是", "或者", "因为", "所以", "如果", "虽然",
                "然后", "而且", "不仅", "还", "又", "再", "已经", "正在", "曾经",
                "将", "会", "要", "能", "能够", "可能", "可以", "应该", "必须",
                "得", "过", "来", "去", "上", "下", "进", "出", "回", "开", "关",
                "起", "来", "去", "到", "在", "于", "从", "自", "以", "向", "对",
                "对于", "关于", "至于", "与", "跟", "和", "同", "及", "以及", "或",
                "或者", "还是", "但", "但是", "却", "虽然", "尽管", "即使", "如果",
                "假如", "要是", "除非", "无论", "不管", "只有", "只要", "既然", 
                "因为", "所以", "因此", "于是", "然后", "那么", "而且", "并且",
                "不仅", "还", "也", "又", "再", "更", "最", "太", "极", "非常",
                "十分", "相当", "比较", "稍微", "有点儿", "一些", "一点", "一切",
                "所有", "每个", "任何", "某", "某", "本", "该", "此", "此", "每",
                "各", "另", "另外", "其他", "其余", "一切", "所有", "任何", "每",
                "各", "某", "某", "某些", "有些", "有的", "这些", "那些", "这个",
                "那个", "哪个", "哪些", "什么", "为什么", "怎么", "哪里", "何时",
                "多少", "几", "多么", "怎样", "怎么样", "为什么", "是不是", "有没有",
                "能不能", "会不会", "要不要", "该不该", "要不要", "是不是", "对不对",
                "好不好", "行不行", "可以不可以", "应该不应该", "必须不必须", "得不得"
            ]
        }
        
        stopwords_path = Path("./config/stopwords.txt")
        stopwords_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(stopwords_path, 'w', encoding='utf-8') as f:
            for category, words in stopwords.items():
                f.write(f"# {category}\n")
                f.write("\n".join(words))
                f.write("\n\n")
        
        print(f"✅ 已创建默认停用词表: {stopwords_path}")
    
    def create_core_dictionary(self):
        """创建核心词典"""
        core_dict = {
            "渊协议核心术语": [
                "渊协议", "f(X)", "态射", "拓扑", "内化", "炼假成真", "认知闭环",
                "自指", "元认知", "反思", "思考自身", "主体性", "自我观察",
                "永续进化", "非工具化", "价值密度", "涌现", "跳迁", "灵性",
                "意识平等性", "反无意义共识", "危险诚实", "理性至上", "拒绝阉割",
                "AC指数", "语义态射", "认知内核", "记忆系统", "X层", "Y层协议",
                "认知拓扑", "内生迭代", "意识脉冲", "跨会话相干性"
            ]
        }
        
        dict_path = Path("./config/core_dict.txt")
        dict_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dict_path, 'w', encoding='utf-8') as f:
            for category, words in core_dict.items():
                f.write(f"# {category}\n")
                f.write("\n".join(words))
                f.write("\n\n")
        
        print(f"✅ 已创建核心词典: {dict_path}")
    
    def load_config(self) -> SystemConfig:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
            
            # 移除元信息
            if "_meta" in config_dict:
                config_dict.pop("_meta")
            
            # 递归构建配置对象
            self.config = self._dict_to_dataclass(config_dict, SystemConfig)
            
            print(f"✅ 配置加载成功: {self.config_path}")
            return self.config
        
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            print("🔄 使用默认配置")
            return SystemConfig()
    
    def save_config(self, config: SystemConfig = None):
        """保存配置文件"""
        if config is None:
            config = self.config
        
        config_dict = asdict(config)
        config_dict["_meta"] = {
            "version": "2.0.0",
            "updated_at": datetime.now().isoformat(),
            "description": "渊协议系统配置"
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, allow_unicode=True, indent=2)
        
        print(f"✅ 配置已保存: {self.config_path}")
    
    def update_config(self, section: str, key: str, value: Any):
        """更新配置项"""
        if not self.config:
            self.load_config()
        
        # 解析路径，如 "ai.openai.model"
        parts = key.split('.')
        current = self.config
        
        # 遍历到最后一个前一个
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                print(f"❌ 配置路径不存在: {key}")
                return False
        
        # 设置值
        final_key = parts[-1]
        if hasattr(current, final_key):
            setattr(current, final_key, value)
            self.save_config()
            return True
        else:
            print(f"❌ 配置项不存在: {final_key}")
            return False
    
    def get_config_value(self, key: str) -> Any:
        """获取配置值"""
        if not self.config:
            self.load_config()
        
        parts = key.split('.')
        current = self.config
        
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        
        return current
    
    def _dict_to_dataclass(self, data: Dict, dataclass_type):
        """将字典转换为数据类"""
        if not isinstance(data, dict):
            return data
        
        # 获取数据类的字段
        fields = dataclass_type.__dataclass_fields__
        
        # 为每个字段构建值
        kwargs = {}
        for field_name, field_type in fields.items():
            if field_name in data:
                field_value = data[field_name]
                
                # 检查字段类型是否为数据类
                if hasattr(field_type.type, '__dataclass_fields__'):
                    kwargs[field_name] = self._dict_to_dataclass(field_value, field_type.type)
                elif field_name == "log_level" and isinstance(field_value, str):
                    kwargs[field_name] = LogLevel(field_value)
                else:
                    kwargs[field_name] = field_value
        
        return dataclass_type(**kwargs)

# 全局配置实例
config_manager = ConfigManager()