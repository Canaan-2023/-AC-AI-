"""
AbyssAC 系统配置
"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Y层记忆库路径
MEMORY_DIR = DATA_DIR / "Y层记忆库"
ID_COUNTER_FILE = MEMORY_DIR / "id_counter.txt"

# 记忆类型目录
META_COGNITION_DIR = MEMORY_DIR / "元认知记忆"
HIGH_LEVEL_DIR = MEMORY_DIR / "高阶整合记忆"
CLASSIFIED_DIR = MEMORY_DIR / "分类记忆"
WORKING_DIR = MEMORY_DIR / "工作记忆"

# 价值层级目录
HIGH_VALUE_DIR = CLASSIFIED_DIR / "高价值"
MEDIUM_VALUE_DIR = CLASSIFIED_DIR / "中价值"
LOW_VALUE_DIR = CLASSIFIED_DIR / "低价值"

# NNG路径
NNG_DIR = DATA_DIR / "nng"
ROOT_NNG = NNG_DIR / "root.json"

# LLM配置
LLM_CONFIG = {
    "provider": "ollama",  # 可选: ollama, lmstudio, openai, anthropic
    "base_url": "http://localhost:11434",  # Ollama默认地址
    "model": "qwen2.5",  # 默认模型
    "api_key": "",  # API方式需要
    "temperature": 0.7,
    "max_tokens": 4096,
}

# DMN触发条件
DMN_TRIGGER = {
    "working_memory_threshold": 20,  # 工作记忆阈值
    "navigation_failure_threshold": 5,  # 导航失败阈值
    "idle_time_seconds": 300,  # 空闲时间(5分钟)
}

# 沙盒配置
SANDBOX_CONFIG = {
    "max_nng_depth": 10,  # NNG最大深度
    "max_memories_per_request": 10,  # 每次请求最大记忆数
}

def ensure_directories():
    """确保所有目录存在"""
    dirs = [
        META_COGNITION_DIR, HIGH_LEVEL_DIR,
        HIGH_VALUE_DIR, MEDIUM_VALUE_DIR, LOW_VALUE_DIR,
        WORKING_DIR, NNG_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def load_config():
    """加载配置（可从文件读取）"""
    ensure_directories()
    return {
        "llm": LLM_CONFIG,
        "dmn_trigger": DMN_TRIGGER,
        "sandbox": SANDBOX_CONFIG,
        "paths": {
            "memory_dir": str(MEMORY_DIR),
            "nng_dir": str(NNG_DIR),
        }
    }
