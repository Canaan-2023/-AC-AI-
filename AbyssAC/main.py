#!/usr/bin/env python3
"""
AbyssAC 主入口

使用方法:
    python main.py              # 启动Gradio界面
    python main.py --cli        # 启动命令行模式
    python main.py --test       # 运行自测
"""

import argparse
import sys
from pathlib import Path

# 确保可以导入本地模块
sys.path.insert(0, str(Path(__file__).parent))


def run_ui():
    """运行Gradio界面"""
    print("启动 AbyssAC Gradio 界面...")
    from ui.gradio_app import main
    main()


def run_cli():
    """运行命令行模式"""
    print("启动 AbyssAC 命令行模式...")
    
    from core.abyssac import AbyssAC
    from core.config import get_config
    
    # 初始化系统
    config = get_config()
    abyssac = AbyssAC(config)
    
    print("\n" + "="*60)
    print("AbyssAC 命令行模式")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'status' 查看系统状态")
    print("输入 'dmn' 手动触发DMN")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("你: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            
            if user_input.lower() == 'status':
                status = abyssac.get_system_status()
                print(f"\n系统状态:")
                for key, value in status.items():
                    print(f"  {key}: {value}")
                print()
                continue
            
            if user_input.lower() == 'dmn':
                result = abyssac.manual_trigger_dmn()
                print(f"\nDMN结果: {result}\n")
                continue
            
            if not user_input:
                continue
            
            # 正常对话
            response = abyssac.chat(user_input)
            print(f"\nAI: {response}\n")
            
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")


def run_tests():
    """运行自测"""
    print("运行 AbyssAC 模块自测...")
    
    import subprocess
    import sys
    
    modules = [
        'core.config',
        'memory.memory_manager',
        'nng.nng_manager',
        'llm.llm_interface',
        'sandbox.sandbox_layer',
        'dmn.dmn_agents',
        'core.abyssac'
    ]
    
    passed = 0
    failed = 0
    
    for module in modules:
        print(f"\n{'='*60}")
        print(f"测试模块: {module}")
        print('='*60)
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', module],
                capture_output=False,
                timeout=60
            )
            if result.returncode == 0:
                print(f"✅ {module} 测试通过")
                passed += 1
            else:
                print(f"❌ {module} 测试失败")
                failed += 1
        except Exception as e:
            print(f"❌ {module} 测试异常: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"自测完成: {passed} 通过, {failed} 失败")
    print('='*60)
    
    return failed == 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AbyssAC - 人工意识系统')
    parser.add_argument('--cli', action='store_true', help='启动命令行模式')
    parser.add_argument('--test', action='store_true', help='运行自测')
    parser.add_argument('--version', action='store_true', help='显示版本')
    
    args = parser.parse_args()
    
    if args.version:
        print("AbyssAC v1.0.0")
        return
    
    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)
    
    if args.cli:
        run_cli()
    else:
        run_ui()


if __name__ == '__main__':
    main()
