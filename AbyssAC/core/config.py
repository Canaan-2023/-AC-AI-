"""
AbyssAC 系统配置管理模块
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class LLMConfig:
    """LLM配置"""
    # 本地LLM配置 (Ollama)
    use_local: bool = True
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"  # 默认使用Qwen2.5 7B，轻量且能力强
    
    # API配置 (备用)
    api_base_url: str = ""
    api_key: str = ""
    api_model: str = ""
    
    # 通用参数
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60


@dataclass
class MemoryConfig:
    """记忆库配置"""
    base_path: str = "Y层记忆库"
    id_counter_file: str = "id_counter.txt"
    
    # 记忆类型目录
    meta_cognition_dir: str = "元认知记忆"
    high_level_dir: str = "高阶整合记忆"
    classified_dir: str = "分类记忆"
    working_dir: str = "工作记忆"
    
    # 价值子目录
    high_value_dir: str = "高价值"
    medium_value_dir: str = "中价值"
    low_value_dir: str = "低价值"


@dataclass
class NNGConfig:
    """NNG导航图配置"""
    base_path: str = "NNG"
    root_file: str = "root.json"
    max_navigation_depth: int = 10
    max_nodes_per_query: int = 3


@dataclass
class DMNConfig:
    """DMN配置"""
    # 触发条件
    working_memory_threshold: int = 20
    navigation_failure_threshold: int = 5
    idle_timeout_seconds: int = 300  # 5分钟
    
    # 日志路径
    navigation_logs_dir: str = "X层/navigation_logs"
    dmn_logs_dir: str = "X层/dmn_logs"


@dataclass
class SystemConfig:
    """系统整体配置"""
    llm: LLMConfig
    memory: MemoryConfig
    nng: NNGConfig
    dmn: DMNConfig
    debug: bool = False


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG_FILE = "abyssac_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_FILE
        self.config: Optional[SystemConfig] = None
        
    def load_config(self) -> SystemConfig:
        """加载配置，如果不存在则创建默认配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.config = SystemConfig(
                    llm=LLMConfig(**data.get('llm', {})),
                    memory=MemoryConfig(**data.get('memory', {})),
                    nng=NNGConfig(**data.get('nng', {})),
                    dmn=DMNConfig(**data.get('dmn', {})),
                    debug=data.get('debug', False)
                )
                print(f"[Config] 已加载配置: {self.config_path}")
            except Exception as e:
                print(f"[Config] 加载配置失败: {e}，使用默认配置")
                self.config = self._create_default_config()
        else:
            print(f"[Config] 配置文件不存在，创建默认配置")
            self.config = self._create_default_config()
            self.save_config()
        return self.config
    
    def _create_default_config(self) -> SystemConfig:
        """创建默认配置"""
        return SystemConfig(
            llm=LLMConfig(),
            memory=MemoryConfig(),
            nng=NNGConfig(),
            dmn=DMNConfig(),
            debug=False
        )
    
    def save_config(self):
        """保存配置到文件"""
        if self.config is None:
            return
        
        data = {
            'llm': asdict(self.config.llm),
            'memory': asdict(self.config.memory),
            'nng': asdict(self.config.nng),
            'dmn': asdict(self.config.dmn),
            'debug': self.config.debug
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Config] 配置已保存: {self.config_path}")
    
    def get_config(self) -> SystemConfig:
        """获取当前配置"""
        if self.config is None:
            return self.load_config()
        return self.config
    
    def update_llm_config(self, **kwargs):
        """更新LLM配置"""
        if self.config:
            for key, value in kwargs.items():
                if hasattr(self.config.llm, key):
                    setattr(self.config.llm, key, value)
            self.save_config()


# 全局配置实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager


def get_config(config_path: Optional[str] = None) -> SystemConfig:
    """获取系统配置便捷函数"""
    return get_config_manager(config_path).get_config()


if __name__ == "__main__":
    # 自测
    print("=" * 50)
    print("Config模块自测")
    print("=" * 50)
    
    # 测试配置加载
    config = get_config()
    print(f"\n[✓] 配置加载成功")
    print(f"  - LLM使用本地: {config.llm.use_local}")
    print(f"  - Ollama模型: {config.llm.ollama_model}")
    print(f"  - 记忆库路径: {config.memory.base_path}")
    print(f"  - NNG路径: {config.nng.base_path}")
    print(f"  - DMN触发阈值: {config.dmn.working_memory_threshold}条工作记忆")
    
    # 测试配置保存
    config_manager = get_config_manager()
    config_manager.update_llm_config(temperature=0.8)
    print(f"\n[✓] 配置更新成功 (temperature=0.8)")
    
    print("\n" + "=" * 50)
    print("Config模块自测通过")
    print("=" * 50)
