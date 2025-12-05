#!/usr/bin/env python3
"""
渊协议v5.2 一键验证+启动脚本（修复子进程编码问题）
"""
import os
import sys
import json
# 直接导入config_check的核心函数，不用子进程调用
import config_check

def print_success(msg: str):
    print(f"\033[92m✅ {msg}\033[0m")

def print_warning(msg: str):
    print(f"\033[93m⚠️ {msg}\033[0m")

def print_error(msg: str):
    print(f"\033[91m❌ {msg}\033[0m")

def fix_json_import() -> bool:
    """检查consciousness_emerge.py的json导入"""
    target_file = "consciousness_emerge.py"
    print(f"\n1. 检查{target_file}导入...")
    
    if not os.path.exists(target_file):
        print_error(f"未找到{target_file}")
        return False
    
    with open(target_file, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f.readlines()]
    
    has_json = any(line.strip().startswith("import json") for line in lines)
    if has_json:
        print_success(f"{target_file}已包含json导入，无需修复")
        return True
    
    # 补充导入（networkx后）
    new_lines = []
    added = False
    for line in lines:
        new_lines.append(line)
        if not added and line.strip().startswith("import networkx"):
            new_lines.insert(len(new_lines), "import json  # 修复JSON依赖")
            added = True
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))
    print_success(f"已为{target_file}补充json导入")
    return True

def verify_be_token_path() -> bool:
    """验证BEtoken配置+自动创建缺失文件"""
    print(f"\n2. 验证BEtoken配置...")
    config_path = "memex_config.json"
    
    if not os.path.exists(config_path):
        print_error(f"未找到{config_path}")
        return False
    
    # 读取配置
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    be_token_path = config_data.get("BE_TOKEN_PATH", "BE_token.json")
    
    # 缺失则创建
    if not os.path.exists(be_token_path):
        with open(be_token_path, "w", encoding="utf-8") as f:
            json.dump({"进度": 0.0, "元块": []}, f, ensure_ascii=False, indent=2)
        print_success(f"自动创建BEtoken文件：{be_token_path}")
    else:
        print_success(f"BEtoken文件已存在：{be_token_path}")
    return True

def run_config_check() -> bool:
    """直接调用config_check的函数，避开子进程编码问题"""
    print(f"\n3. 检查系统配置...")
    try:
        # 直接调用config_check.py里的check_config函数
        config_check.check_config()
        print_success("配置检查通过！")
        return True
    except Exception as e:
        print_error(f"配置检查失败：{str(e)}")
        return False

def generate_placeholder() -> bool:
    """生成占位图"""
    print(f"\n4. 生成记忆占位图...")
    if not os.path.exists("generate_placeholder_img.py"):
        print_error("未找到generate_placeholder_img.py")
        return False
    
    try:
        # 直接导入调用（避免子进程编码问题）
        import generate_placeholder_img
        generate_placeholder_img.generate()
        print_success("占位图生成完成！")
        return True
    except Exception as e:
        print_error(f"生成占位图失败：{str(e)}")
        return False

def start_system() -> bool:
    """启动main.py"""
    print(f"\n5. 启动渊协议v5.2...\n")
    if not os.path.exists("main.py"):
        print_error("未找到main.py")
        return False
    
    try:
        # 直接运行main.py（避免子进程编码问题）
        import main
        main.run()
        return True
    except Exception as e:
        print_error(f"启动系统失败：{str(e)}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("渊协议v5.2 一键启动流程")
    print("="*50)
    
    steps = [
        fix_json_import,
        verify_be_token_path,
        run_config_check,
        generate_placeholder,
        start_system
    ]
    
    all_success = True
    for step in steps:
        if not step():
            all_success = False
            print_warning("部分步骤失败，尝试继续启动...")
    
    if all_success:
        print("\n" + "="*50)
        print_success("系统启动成功！请在交互界面操作")
        print("="*50)
    else:
        print("\n" + "="*50)
        print_warning("系统已启动，但部分前置步骤有问题，建议检查日志")
        print("="*50)