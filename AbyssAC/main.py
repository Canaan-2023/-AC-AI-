#!/usr/bin/env python3
"""
AbyssAC - 人工意识系统
主入口文件

使用方法:
    python main.py              # 启动Gradio界面
    python main.py --cli        # 启动命令行交互
    python main.py --test       # 运行自测
"""
import argparse
import sys
from pathlib import Path

# 确保可以导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

from core.system import get_system
from config import LLM_CONFIG


def run_gradio():
    """运行Gradio界面"""
    print("🚀 启动AbyssAC Gradio界面...")
    try:
        from frontend.app import main
        main()
    except ImportError as e:
        print(f"❌ 启动失败: {e}")
        print("请确保已安装Gradio: pip install gradio")


def run_cli():
    """运行命令行交互"""
    print("🚀 启动AbyssAC命令行模式...")
    
    system = get_system()
    
    # 初始化
    print("\n正在初始化系统...")
    print(f"LLM配置: {LLM_CONFIG['provider']} @ {LLM_CONFIG['base_url']}")
    print(f"模型: {LLM_CONFIG['model']}")
    
    success = system.initialize()
    if not success:
        print("❌ 系统初始化失败")
        return
    
    # 测试LLM连接
    print("\n测试LLM连接...")
    if system.test_llm_connection():
        print("✅ LLM连接正常")
    else:
        print("⚠️ LLM连接测试失败，请检查配置")
        return
    
    print("\n" + "="*50)
    print("AbyssAC 命令行模式已启动")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'status' 查看系统状态")
    print("输入 'dmn' 手动触发DMN")
    print("="*50 + "\n")
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 再见!")
                break
            
            if user_input.lower() == 'status':
                status = system.get_system_status()
                print(f"\n📊 系统状态:")
                for k, v in status.items():
                    print(f"  {k}: {v}")
                continue
            
            if user_input.lower() == 'dmn':
                print("\n🔄 手动触发DMN...")
                success, logs = system.manual_dmn("记忆整合")
                print(logs)
                continue
            
            # 正常对话
            print("\n🤖 AI思考中...")
            response = system.chat(user_input)
            
            print(f"\n🤖 AI: {response.content}")
            
            if response.dmn_triggered:
                print(f"\n🔄 DMN已触发")
            
            if response.sandbox_logs:
                print(f"\n📋 沙盒日志:\n{response.sandbox_logs[:500]}...")
                
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


def run_tests():
    """运行自测"""
    print("🧪 运行AbyssAC自测...\n")
    
    import unittest
    from tests.test_all import run_all_tests
    
    success = run_all_tests()
    
    if success:
        print("\n✅ 所有测试通过!")
        return 0
    else:
        print("\n❌ 部分测试失败")
        return 1


def main():
    parser = argparse.ArgumentParser(description='AbyssAC - 人工意识系统')
    parser.add_argument('--cli', action='store_true', help='启动命令行模式')
    parser.add_argument('--test', action='store_true', help='运行自测')
    parser.add_argument('--provider', type=str, default='ollama', help='LLM Provider')
    parser.add_argument('--model', type=str, default='qwen2.5', help='模型名称')
    parser.add_argument('--url', type=str, default='http://localhost:11434', help='LLM服务地址')
    
    args = parser.parse_args()
    
    # 更新配置
    if args.provider:
        LLM_CONFIG['provider'] = args.provider
    if args.model:
        LLM_CONFIG['model'] = args.model
    if args.url:
        LLM_CONFIG['base_url'] = args.url
    
    if args.test:
        return run_tests()
    elif args.cli:
        run_cli()
    else:
        run_gradio()


if __name__ == "__main__":
    sys.exit(main())
