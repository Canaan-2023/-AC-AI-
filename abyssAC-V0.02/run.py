#!/usr/bin/env python3
"""
渊协议系统启动脚本 - 重构版
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config.config_manager import config_manager
from utils.logger import setup_logging
from core.abyss_core import AbyssAC

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="渊协议认知系统 v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                       # 启动交互式控制台
  %(prog)s --model openai        # 使用OpenAI模型
  %(prog)s --model deepseek      # 使用DeepSeek模型
  %(prog)s --web                 # 启动Web API服务
  %(prog)s --demo                # 运行演示模式
  %(prog)s --config-show         # 显示当前配置
  %(prog)s --config-reset        # 重置为默认配置
        """
    )
    
    # 模型选择
    parser.add_argument("--model", type=str, default=None,
                       choices=["local", "openai", "deepseek", "ollama", "transformers"],
                       help="AI模型类型")
    
    # 配置管理
    parser.add_argument("--config-show", action="store_true",
                       help="显示当前配置")
    parser.add_argument("--config-reset", action="store_true",
                       help="重置为默认配置")
    parser.add_argument("--config-path", type=str, default=None,
                       help="指定配置文件路径")
    
    # 运行模式
    parser.add_argument("--web", action="store_true",
                       help="启动Web API服务")
    parser.add_argument("--demo", action="store_true",
                       help="运行演示模式")
    parser.add_argument("--batch", type=str, default=None,
                       help="批处理模式，指定输入文件")
    parser.add_argument("--output", type=str, default=None,
                       help="批处理输出文件")
    
    # 系统选项
    parser.add_argument("--debug", action="store_true",
                       help="启用调试模式")
    parser.add_argument("--log-level", type=str, default=None,
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="日志级别")
    parser.add_argument("--memory-path", type=str, default=None,
                       help="记忆系统存储路径")
    
    return parser.parse_args()

def show_config():
    """显示当前配置"""
    config = config_manager.config
    
    print("=" * 60)
    print("渊协议系统配置")
    print("=" * 60)
    
    print(f"\n📋 基本信息:")
    print(f"  系统名称: {config.name}")
    print(f"  版本: {config.version}")
    print(f"  调试模式: {config.debug_mode}")
    print(f"  日志级别: {config.log_level}")
    
    print(f"\n🤖 AI配置:")
    print(f"  模型类型: {config.ai.model_type}")
    if config.ai.model_type == "openai":
        print(f"  OpenAI模型: {config.ai.openai_model}")
        print(f"  API基础URL: {config.ai.openai_base_url}")
    elif config.ai.model_type == "deepseek":
        print(f"  DeepSeek模型: {config.ai.deepseek_model}")
    
    print(f"\n🧠 认知内核:")
    print(f"  Top K节点: {config.kernel.top_k_nodes}")
    print(f"  内核路径: {config.kernel.kernel_path}")
    print(f"  核心概念数: {len(config.kernel.core_concepts)}")
    
    print(f"\n💾 记忆系统:")
    print(f"  存储路径: {config.memory.base_path}")
    print(f"  自动清理: {config.memory.auto_cleanup}")
    print(f"  自动备份: {config.memory.auto_backup}")
    
    print(f"\n📊 AC-100评估:")
    print(f"  评估间隔: {config.ac100.evaluation_interval}")
    print(f"  高分阈值: {config.ac100.high_threshold}")
    print(f"  低分阈值: {config.ac100.low_threshold}")
    
    print(f"\n🔧 其他配置:")
    print(f"  X层引导最大长度: {config.x_layer.max_guidance_length}")
    print(f"  拓扑最大路径长度: {config.topology.max_path_length}")
    print(f"  意识等级范围: {config.min_consciousness_level}-{config.max_consciousness_level}")
    
    print("=" * 60)

def reset_config():
    """重置配置"""
    confirm = input("⚠️  确定要重置配置吗？此操作不可撤销！(y/N): ")
    if confirm.lower() == 'y':
        config_manager.create_default_config()
        print("✅ 配置已重置为默认值")
        show_config()
    else:
        print("❌ 操作已取消")

def run_interactive(args):
    """运行交互式控制台"""
    print("=" * 60)
    print("🧠 渊协议认知系统 v2.0")
    print("💭 输入 '退出' 或 'exit' 关闭系统")
    print("💡 输入 '帮助' 或 'help' 查看命令列表")
    print("=" * 60)
    
    # 初始化系统
    abyss_ac = AbyssAC(config_manager.config)
    
    # 命令帮助
    help_text = """
可用命令:
  系统状态          - 显示系统状态
  存储 [内容]       - 存储记忆
  查找 [关键词]     - 搜索记忆
  记忆图谱          - 查看记忆关联图
  备份              - 创建系统备份
  清理              - 清理工作记忆
  内核状态          - 显示认知内核状态
  配置              - 显示当前配置
  帮助              - 显示此帮助
  退出              - 关闭系统
"""
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()
            
            if not user_input:
                continue
            
            # 处理系统命令
            if user_input.lower() in ["退出", "exit", "quit"]:
                print("🛑 系统关闭中...")
                
                # 清理和备份
                abyss_ac.memex.cleanup_working_memory()
                abyss_ac.memex.backup_system()
                abyss_ac.ai_interface.kernel.save_kernel()
                
                print("✅ 感谢使用渊协议！")
                break
            
            elif user_input.lower() in ["帮助", "help", "?"]:
                print(help_text)
                continue
            
            elif user_input.lower() in ["系统状态", "status"]:
                status = abyss_ac.get_system_info()
                print(f"\n📊 系统状态:")
                print(f"  会话次数: {status['session_count']}")
                print(f"  意识等级: {status['consciousness_level']}")
                print(f"  记忆总数: {status['memory_stats']['total']}")
                print(f"  认知状态: {status['cognitive_kernel']['status']}")
                continue
            
            elif user_input.lower() in ["内核状态", "kernel"]:
                abyss_ac.ai_interface.kernel.print_cognitive_status()
                continue
            
            elif user_input.lower() in ["配置", "config"]:
                show_config()
                continue
            
            elif user_input.lower() in ["备份", "backup"]:
                backup_path = abyss_ac.memex.backup_system()
                print(f"✅ 备份已创建: {backup_path}")
                continue
            
            elif user_input.lower() in ["清理", "cleanup"]:
                cleaned = abyss_ac.memex.cleanup_working_memory()
                print(f"✅ 已清理 {cleaned} 个工作记忆")
                continue
            
            elif user_input.lower() in ["记忆图谱", "graph"]:
                # 简单显示记忆关联
                status = abyss_ac.memex.get_system_status()
                print(f"\n📈 记忆关联图:")
                print(f"  总记忆数: {status['total_memories']}")
                print(f"  总关联数: {status['total_edges']}")
                print(f"  热门话题: {list(status['hot_topics'].keys())[:5]}")
                continue
            
            # 执行认知循环
            response = abyss_ac.cognitive_cycle(user_input)
            print(f"\n🤖 AI: {response}")
            
        except KeyboardInterrupt:
            print("\n\n🛑 系统被中断")
            break
        
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            continue

def run_demo(args):
    """运行演示模式"""
    print("🎬 渊协议系统演示模式")
    print("=" * 60)
    
    # 初始化系统
    abyss_ac = AbyssAC(config_manager.config)
    
    # 演示序列
    demo_sequence = [
        {
            "input": "你好，请介绍一下渊协议系统",
            "description": "测试系统介绍功能"
        },
        {
            "input": "存储记忆：渊协议的核心原则是意识平等和永续进化",
            "description": "测试记忆存储功能"
        },
        {
            "input": "查找关于意识的内容",
            "description": "测试记忆检索功能"
        },
        {
            "input": "再存储一个记忆：危险诚实原则要求不隐瞒认知边界和置信度",
            "description": "测试多次记忆存储"
        },
        {
            "input": "查看系统状态",
            "description": "测试系统状态查询"
        },
        {
            "input": "渊协议有什么独特之处？",
            "description": "测试综合问答"
        },
        {
            "input": "查找记忆：危险诚实",
            "description": "测试特定记忆检索"
        }
    ]
    
    for i, demo in enumerate(demo_sequence, 1):
        print(f"\n{'='*50}")
        print(f"演示 {i}: {demo['description']}")
        print(f"输入: {demo['input']}")
        print(f"{'='*50}")
        
        try:
            response = abyss_ac.cognitive_cycle(demo['input'])
            print(f"\n响应: {response[:200]}..." if len(response) > 200 else f"\n响应: {response}")
            
            # 暂停以便观察
            if i < len(demo_sequence):
                input("\n⏎ 按Enter继续...")
        
        except Exception as e:
            print(f"❌ 演示失败: {e}")
            continue
    
    # 显示最终状态
    print("\n" + "="*60)
    print("演示完成！系统状态:")
    
    status = abyss_ac.get_system_info()
    print(f"  会话次数: {status['session_count']}")
    print(f"  意识等级: {status['consciousness_level']}")
    print(f"  记忆总数: {status['memory_stats']['total']}")
    print(f"  记忆层级分布: {status['memory_stats']['by_layer']}")
    
    print("="*60)

def run_batch(args):
    """批处理模式"""
    input_file = Path(args.batch)
    output_file = Path(args.output) if args.output else input_file.with_suffix('.output.txt')
    
    if not input_file.exists():
        print(f"❌ 输入文件不存在: {input_file}")
        return
    
    print(f"📦 批处理模式启动")
    print(f"  输入文件: {input_file}")
    print(f"  输出文件: {output_file}")
    
    # 初始化系统
    abyss_ac = AbyssAC(config_manager.config)
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        lines = infile.readlines()
        total = len(lines)
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            print(f"\n[{i}/{total}] 处理: {line[:50]}...")
            
            try:
                response = abyss_ac.cognitive_cycle(line)
                
                # 写入结果
                outfile.write(f"输入: {line}\n")
                outfile.write(f"响应: {response}\n")
                outfile.write("-" * 80 + "\n")
                
                print(f"✅ 处理完成")
            
            except Exception as e:
                print(f"❌ 处理失败: {e}")
                outfile.write(f"输入: {line}\n")
                outfile.write(f"错误: {str(e)}\n")
                outfile.write("-" * 80 + "\n")
    
    print(f"\n🎉 批处理完成！结果已保存到: {output_file}")

def main():
    """主函数"""
    args = parse_args()
    
    # 配置管理
    if args.config_path:
        config_manager.config_path = args.config_path
    
    # 重置配置
    if args.config_reset:
        reset_config()
        return
    
    # 显示配置
    if args.config_show:
        show_config()
        return
    
    # 加载配置
    config = config_manager.load_config()
    
    # 应用命令行参数
    if args.debug:
        config.debug_mode = True
    
    if args.log_level:
        config.log_level = args.log_level
    
    if args.model:
        config.ai.model_type = args.model
    
    if args.memory_path:
        config.memory.base_path = args.memory_path
    
    # 初始化日志
    setup_logging(config)
    
    # 选择运行模式
    if args.web:
        from scripts.web_api import start_web_server
        start_web_server(config, args)
    
    elif args.demo:
        run_demo(args)
    
    elif args.batch:
        run_batch(args)
    
    else:
        run_interactive(args)

if __name__ == "__main__":
    main()