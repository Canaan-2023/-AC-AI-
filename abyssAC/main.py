#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
渊协议MCP插件系统 - 主入口

启动和管理整个系统的主程序。
"""

import sys
import os
import signal
import argparse
import json
from pathlib import Path

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from abyss_mcp_plugin import AbyssKernel
from abyss_mcp_plugin.core.config_manager import config
from abyss_mcp_plugin.core.logger import AbyssLogger


def setup_signal_handlers(kernel):
    """设置信号处理器"""
    def signal_handler(signum, frame):
        print("\n收到终止信号，正在优雅关闭...")
        kernel.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def interactive_mode(kernel):
    """交互模式"""
    print("\n" + "=" * 60)
    print("渊协议MCP插件系统 - 交互模式")
    print("=" * 60)
    print("\n可用命令:")
    print("  process <text>     - 处理文本")
    print("  search <query>     - 搜索记忆")
    print("  add_word <word>    - 添加词到字典")
    print("  stats              - 显示系统统计")
    print("  save               - 保存系统状态")
    print("  load               - 加载系统状态")
    print("  help               - 显示帮助")
    print("  exit               - 退出程序")
    print("=" * 60)
    
    while True:
        try:
            command = input("\nabyss_mcp> ").strip()
            
            if not command:
                continue
            
            parts = command.split(maxsplit=1)
            cmd = parts[0].lower()
            
            if cmd == 'exit' or cmd == 'quit':
                print("再见！")
                break
            
            elif cmd == 'help':
                print("\n可用命令:")
                print("  process <text>     - 处理文本")
                print("  search <query>     - 搜索记忆")
                print("  add_word <word>    - 添加词到字典")
                print("  stats              - 显示系统统计")
                print("  save               - 保存系统状态")
                print("  load               - 加载系统状态")
                print("  help               - 显示帮助")
                print("  exit               - 退出程序")
            
            elif cmd == 'process' and len(parts) > 1:
                result = kernel.process(parts[1])
                print(f"\n结果:")
                print(json.dumps(result, ensure_ascii=False, indent=2))
            
            elif cmd == 'search' and len(parts) > 1:
                results = kernel.memory.retrieve_memory(parts[1], limit=5)
                print(f"\n找到 {len(results)} 个结果:")
                for i, mem in enumerate(results, 1):
                    print(f"  {i}. {mem.id}: {mem.content[:60]}...")
            
            elif cmd == 'add_word' and len(parts) > 1:
                dict_id = kernel.dict_manager.add_word(parts[1])
                print(f"✅ 词已添加到字典: {dict_id}")
            
            elif cmd == 'stats':
                stats = kernel.get_stats()
                print(f"\n系统统计:")
                print(json.dumps(stats, ensure_ascii=False, indent=2))
            
            elif cmd == 'save':
                success = kernel.save_state()
                print(f"✅ 状态已保存: {success}")
            
            elif cmd == 'load':
                success = kernel.load_state()
                print(f"✅ 状态已加载: {success}")
            
            else:
                print(f"❌ 未知命令: {cmd}")
                print("输入 'help' 查看可用命令")
                
        except KeyboardInterrupt:
            print("\n使用 'exit' 命令退出")
        except Exception as e:
            print(f"❌ 错误: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='渊协议MCP插件系统 - 模型-控制器-插件架构',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python main.py --interactive                    # 交互模式
  python main.py --process "示例文本"           # 处理文本
  python main.py --config ./config/custom.json    # 使用自定义配置
  python main.py --daemon                         # 守护进程模式
        '''
    )
    
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='启动交互模式')
    parser.add_argument('--process', '-p', type=str,
                        help='处理指定文本')
    parser.add_argument('--config', '-c', type=str,
                        help='使用指定的配置文件')
    parser.add_argument('--daemon', '-d', action='store_true',
                        help='以守护进程模式运行')
    parser.add_argument('--save-state', type=str,
                        help='保存状态到指定文件')
    parser.add_argument('--load-state', type=str,
                        help='从指定文件加载状态')
    parser.add_argument('--stats', action='store_true',
                        help='显示系统统计')
    parser.add_argument('--examples', action='store_true',
                        help='运行示例代码')
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config:
        print(f"加载配置文件: {args.config}")
        config.update_from_file(args.config)
    
    # 创建内核
    kernel = AbyssKernel()
    
    # 设置信号处理器
    setup_signal_handlers(kernel)
    
    try:
        # 加载状态
        if args.load_state:
            print(f"加载状态: {args.load_state}")
            kernel.load_state(args.load_state)
        
        # 初始化
        print("初始化系统...")
        kernel.initialize()
        
        # 显示统计
        if args.stats:
            stats = kernel.get_stats()
            print("\n系统统计:")
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        
        # 处理文本
        if args.process:
            print(f"\n处理文本: {args.process}")
            result = kernel.process(args.process, return_metadata=True)
            print("\n结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        
        # 运行示例
        if args.examples:
            print("\n运行示例代码...")
            from examples.basic_usage import (
                example_1_basic_processing,
                example_2_memory_operations,
                example_3_dictionary_operations
            )
            
            example_1_basic_processing()
            example_2_memory_operations()
            example_3_dictionary_operations()
        
        # 保存状态
        if args.save_state:
            print(f"\n保存状态: {args.save_state}")
            kernel.save_state(args.save_state)
        
        # 守护进程模式
        if args.daemon:
            print("\n守护进程模式已启动，按Ctrl+C退出")
            while True:
                time.sleep(1)
        
        # 交互模式
        elif args.interactive:
            interactive_mode(kernel)
        
        # 单次执行模式
        else:
            if not (args.process or args.stats or args.examples or args.save_state):
                parser.print_help()
    
    except KeyboardInterrupt:
        print("\n收到中断信号")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n清理系统资源...")
        kernel.cleanup()
        print("✅ 系统已安全关闭")


if __name__ == "__main__":
    main()