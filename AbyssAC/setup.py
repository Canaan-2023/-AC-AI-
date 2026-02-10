"""AbyssAC 系统初始化脚本

用于初始化系统目录结构和基础文件。
"""

import os
import json
from datetime import datetime


def init_system(base_path: str = ".") -> bool:
    """
    初始化AbyssAC系统
    
    Args:
        base_path: 系统基础路径
    
    Returns:
        是否初始化成功
    """
    print("=" * 50)
    print("AbyssAC 系统初始化")
    print("=" * 50)
    
    # 创建目录结构
    dirs = [
        "core",
        "llm",
        "utils",
        "storage/Y层记忆库/元认知记忆",
        "storage/Y层记忆库/高阶整合记忆",
        "storage/Y层记忆库/分类记忆/高价值",
        "storage/Y层记忆库/分类记忆/中价值",
        "storage/Y层记忆库/分类记忆/低价值",
        "storage/Y层记忆库/工作记忆",
        "storage/nng",
        "storage/system/logs",
        "tests",
        "examples",
    ]
    
    print("\n创建目录结构...")
    for d in dirs:
        path = os.path.join(base_path, d)
        os.makedirs(path, exist_ok=True)
        print(f"  ✓ {d}")
    
    # 创建root.json
    root_file = os.path.join(base_path, "storage/nng/root.json")
    if not os.path.exists(root_file):
        print("\n创建 root.json...")
        with open(root_file, 'w', encoding='utf-8') as f:
            json.dump({
                "一级节点": [],
                "更新时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {root_file}")
    
    # 创建memory_counter.txt
    counter_file = os.path.join(base_path, "storage/system/memory_counter.txt")
    if not os.path.exists(counter_file):
        print("\n创建 memory_counter.txt...")
        with open(counter_file, 'w', encoding='utf-8') as f:
            f.write("0")
        print(f"  ✓ {counter_file}")
    
    # 创建memory_metadata.json
    metadata_file = os.path.join(base_path, "storage/system/memory_metadata.json")
    if not os.path.exists(metadata_file):
        print("\n创建 memory_metadata.json...")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {metadata_file}")
    
    # 创建config.json（如果不存在）
    config_file = os.path.join(base_path, "config.json")
    if not os.path.exists(config_file):
        print("\n创建 config.json...")
        config = {
            "llm": {
                "api_type": "ollama",
                "base_url": "http://localhost:11434",
                "model": "qwen2.5:latest",
                "temperature": 0.7,
                "max_tokens": 2000,
                "timeout": 30,
                "retry_count": 3
            },
            "system": {
                "max_navigation_depth": 10,
                "navigation_timeout": 30,
                "dmn_auto_trigger": True,
                "dmn_idle_threshold": 300,
                "dmn_memory_threshold": 20,
                "dmn_failure_threshold": 5,
                "max_working_memory": 50
            },
            "paths": {
                "base": os.path.abspath(base_path),
                "y_layer": "storage/Y层记忆库",
                "nng": "storage/nng",
                "system": "storage/system",
                "logs": "storage/system/logs"
            },
            "confidence": {
                "display_threshold": 30,
                "delete_threshold": 10,
                "default_new": 70
            }
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"  ✓ {config_file}")
    
    print("\n" + "=" * 50)
    print("系统初始化完成！")
    print("=" * 50)
    print(f"\n请编辑 {config_file} 配置您的LLM服务")
    print(f"然后运行: python main.py")
    
    return True


if __name__ == "__main__":
    import sys
    
    base_path = sys.argv[1] if len(sys.argv) > 1 else "."
    init_system(base_path)
