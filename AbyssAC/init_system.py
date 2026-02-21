"""
AbyssAC System Initialization
系统初始化脚本 - 创建必要的目录结构和初始数据
"""

import os
import json
import sys


def create_directory_structure():
    """创建目录结构"""
    print("[初始化] 创建目录结构...")
    
    directories = [
        # NNG目录
        "storage/nng",
        
        # Y层记忆库目录
        "storage/Y层记忆库/元认知记忆",
        "storage/Y层记忆库/高阶整合记忆",
        "storage/Y层记忆库/分类记忆/高价值",
        "storage/Y层记忆库/分类记忆/中价值",
        "storage/Y层记忆库/分类记忆/低价值",
        "storage/Y层记忆库/工作记忆",
        
        # 其他目录
        "storage/AI开发空间",
        "storage/沙箱",
        "temp",
        "X层/navigation_logs",
        "logs",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  创建: {directory}")
    
    print("[初始化] 目录结构创建完成")


def create_root_nng():
    """创建root.json"""
    print("[初始化] 创建root.json...")
    
    root_path = "storage/nng/root.json"
    
    if os.path.exists(root_path):
        print(f"  已存在: {root_path}")
        return
    
    from datetime import datetime
    
    root_data = {
        "一级节点": [],
        "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(root_path, 'w', encoding='utf-8') as f:
        json.dump(root_data, f, ensure_ascii=False, indent=2)
    
    print(f"  创建: {root_path}")


def create_example_nng_nodes():
    """创建示例NNG节点"""
    print("[初始化] 创建示例NNG节点...")
    
    from datetime import datetime
    
    # 示例节点
    example_nodes = [
        {
            "id": "1",
            "content": "系统核心概念与架构",
            "parent": None
        },
        {
            "id": "2",
            "content": "用户交互与界面设计",
            "parent": None
        },
        {
            "id": "3",
            "content": "记忆管理与存储策略",
            "parent": None
        }
    ]
    
    for node in example_nodes:
        node_path = f"storage/nng/{node['id']}"
        json_path = f"{node_path}/{node['id']}.json"
        
        if os.path.exists(json_path):
            print(f"  已存在: {json_path}")
            continue
        
        os.makedirs(node_path, exist_ok=True)
        
        node_data = {
            "定位": node["id"],
            "置信度": 1.0,
            "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "内容": node["content"],
            "上级关联NNG": [],
            "下级关联NNG": [],
            "关联的记忆文件摘要": []
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(node_data, f, ensure_ascii=False, indent=2)
        
        print(f"  创建: {json_path}")
    
    # 更新root.json
    root_path = "storage/nng/root.json"
    if os.path.exists(root_path):
        with open(root_path, 'r', encoding='utf-8') as f:
            root_data = json.load(f)
        
        for node in example_nodes:
            entry = f"{node['id']}（{node['content']}）"
            if entry not in root_data["一级节点"]:
                root_data["一级节点"].append(entry)
        
        root_data["更新时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(root_path, 'w', encoding='utf-8') as f:
            json.dump(root_data, f, ensure_ascii=False, indent=2)
        
        print(f"  更新: {root_path}")


def create_example_memories():
    """创建示例记忆"""
    print("[初始化] 创建示例记忆...")
    
    from datetime import datetime
    
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    day = datetime.now().strftime("%d")
    
    # 示例记忆
    example_memories = [
        {
            "id": "1",
            "type": "分类记忆",
            "level": "高价值",
            "user": "什么是AbyssAC？",
            "ai": "AbyssAC（渊协议）是一个AI自主意识架构，通过NNG导航图和Y层记忆库构建AI的认知系统。",
            "confidence": 0.95
        }
    ]
    
    for mem in example_memories:
        mem_path = f"storage/Y层记忆库/{mem['type']}/{mem['level']}/{year}/{month}/{day}"
        os.makedirs(mem_path, exist_ok=True)
        
        file_path = f"{mem_path}/{mem['id']}.txt"
        
        if os.path.exists(file_path):
            print(f"  已存在: {file_path}")
            continue
        
        content = f"""【记忆层级】：{mem['type']}
【记忆ID】：{mem['id']}
【记忆时间】：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
【置信度】：{mem['confidence']}
【核心内容】：
用户输入：{mem['user']}
AI响应：{mem['ai']}"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  创建: {file_path}")


def create_init_files():
    """创建__init__.py文件"""
    print("[初始化] 创建__init__.py文件...")
    
    init_files = [
        "core/__init__.py",
        "config/__init__.py",
        "ui/__init__.py"
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write("# AbyssAC Module\n")
            print(f"  创建: {init_file}")


def check_dependencies():
    """检查依赖"""
    print("[初始化] 检查依赖...")
    
    required = {
        'requests': 'requests',
        'PyQt6': 'PyQt6'
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (未安装)")
            missing.append(package)
    
    if missing:
        print(f"\n[警告] 缺少以下依赖，请运行: pip install {' '.join(missing)}")
        return False
    
    print("[初始化] 所有依赖已安装")
    return True


def main():
    """主函数"""
    print("="*60)
    print("  AbyssAC 系统初始化")
    print("="*60)
    print()
    
    try:
        # 检查依赖
        check_dependencies()
        print()
        
        # 创建目录结构
        create_directory_structure()
        print()
        
        # 创建__init__.py
        create_init_files()
        print()
        
        # 创建root.json
        create_root_nng()
        print()
        
        # 创建示例NNG节点
        create_example_nng_nodes()
        print()
        
        # 创建示例记忆
        create_example_memories()
        print()
        
        print("="*60)
        print("  初始化完成！")
        print("="*60)
        print()
        print("使用方法:")
        print("  1. 命令行模式: python cli.py")
        print("  2. GUI模式: python ui/main_window.py")
        print()
        print("注意: 请确保已安装并运行LLM服务（如Ollama）")
        print("      默认API地址: http://localhost:11434")
        print()
        
    except Exception as e:
        print(f"[错误] 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
