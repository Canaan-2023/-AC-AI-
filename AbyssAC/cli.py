"""
AbyssAC Command Line Interface
AbyssAC命令行界面
"""

import os
import sys
import argparse
import json
from typing import Optional

from core.main_system import get_system, init_system
from core.nng_manager import get_nng_manager
from core.memory_manager import get_memory_manager
from core.ai_dev_space import get_dev_space, get_sandbox
from core.quick_thinking import get_quick_system
from core.dmn_system import get_dmn_system, DMNTaskType
from config.system_config import get_config


class AbyssACCLI:
    """AbyssAC命令行界面"""
    
    def __init__(self):
        self.system = None
    
    def init_system(self):
        """初始化系统"""
        print("[AbyssAC] 正在初始化系统...")
        self.system = init_system()
        print("[AbyssAC] 系统初始化完成")
    
    def chat(self, message: str, slow: bool = False):
        """发送消息"""
        if not self.system:
            self.init_system()
        
        print(f"\n用户: {message}\n")
        print("AI正在思考...\n")
        
        result = self.system.process_input(message, use_sandbox=slow)
        
        if result["success"]:
            print(f"AI: {result['response']}\n")
            
            if result.get("used_quick"):
                print("[使用快思考]")
            elif result.get("used_sandbox"):
                print("[使用慢思考 - 三层沙盒]")
        else:
            print(f"[错误] {result['error']}")
    
    def interactive_mode(self):
        """交互模式"""
        if not self.system:
            self.init_system()
        
        print("\n" + "="*50)
        print("  AbyssAC - 渊协议 交互模式")
        print("  输入 'quit' 或 'exit' 退出")
        print("  输入 '/slow' 切换慢思考模式")
        print("  输入 '/fast' 切换快思考模式")
        print("  输入 '/status' 查看系统状态")
        print("  输入 '/dmn' 运行DMN维护")
        print("="*50 + "\n")
        
        slow_mode = False
        
        while True:
            try:
                user_input = input("> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("再见！")
                    break
                
                if user_input == '/slow':
                    slow_mode = True
                    print("[已切换到慢思考模式]")
                    continue
                
                if user_input == '/fast':
                    slow_mode = False
                    print("[已切换到快思考模式]")
                    continue
                
                if user_input == '/status':
                    self.show_status()
                    continue
                
                if user_input == '/dmn':
                    self.run_dmn()
                    continue
                
                if user_input == '/help':
                    self.show_help()
                    continue
                
                self.chat(user_input, slow=slow_mode)
                
            except KeyboardInterrupt:
                print("\n再见！")
                break
            except EOFError:
                break
    
    def show_status(self):
        """显示系统状态"""
        if not self.system:
            self.init_system()
        
        status = self.system.get_system_status()
        
        print("\n--- 系统状态 ---")
        print(f"记忆计数器: {status['memory_counter']}")
        print(f"NNG节点数: {status['nng_nodes']}")
        print(f"工作记忆数: {status['work_memories']}")
        print(f"对话次数: {status['conversation_count']}")
        print(f"LLM连接: {'已连接' if status['llm_connected'] else '未连接'}")
        print("----------------\n")
    
    def run_dmn(self):
        """运行DMN维护"""
        if not self.system:
            self.init_system()
        
        print("\n[DMN] 运行维护任务...")
        results = self.system.run_dmn_maintenance()
        
        print(f"[DMN] 完成 {len(results)} 个任务")
        for result in results:
            print(f"  - 任务 {result['task_id']}: {'成功' if result['success'] else '失败'}")
        print()
    
    def show_help(self):
        """显示帮助"""
        print("\n--- 命令帮助 ---")
        print("quit, exit, q - 退出程序")
        print("/slow         - 切换到慢思考模式")
        print("/fast         - 切换到快思考模式")
        print("/status       - 查看系统状态")
        print("/dmn          - 运行DMN维护")
        print("/help         - 显示帮助")
        print("----------------\n")
    
    def list_nng(self):
        """列出NNG节点"""
        if not self.system:
            self.init_system()
        
        nng_manager = get_nng_manager()
        nodes = nng_manager.list_all_nodes()
        
        print(f"\n--- NNG节点列表 ({len(nodes)}个) ---")
        for node_id in nodes[:20]:  # 限制显示数量
            node = nng_manager.read_node(node_id)
            if node:
                content = node.content[:40] + "..." if len(node.content) > 40 else node.content
                print(f"  {node_id}: {content}")
        print()
    
    def list_memories(self, memory_type: str = None):
        """列出记忆"""
        if not self.system:
            self.init_system()
        
        memory_manager = get_memory_manager()
        memories = memory_manager.list_memories(memory_type=memory_type, limit=20)
        
        print(f"\n--- 记忆列表 ({len(memories)}条) ---")
        for mem in memories:
            print(f"  [{mem['memory_id']}] {mem['type']} (置信度: {mem['confidence']:.2f})")
            print(f"    {mem['user_input'][:60]}...")
        print()
    
    def create_nng(self, node_id: str, content: str, parent_id: str = None):
        """创建NNG节点"""
        if not self.system:
            self.init_system()
        
        success = self.system.create_nng_node(node_id, content, parent_id)
        
        if success:
            print(f"[成功] 创建NNG节点: {node_id}")
        else:
            print(f"[失败] 无法创建NNG节点: {node_id}")
    
    def export_memory(self, memory_id: str, filepath: str):
        """导出记忆"""
        if not self.system:
            self.init_system()
        
        success = self.system.export_memory(memory_id, filepath)
        
        if success:
            print(f"[成功] 记忆已导出到: {filepath}")
        else:
            print(f"[失败] 无法导出记忆: {memory_id}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AbyssAC - AI自主意识系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py                    # 启动交互模式
  python cli.py -c "你好"          # 发送单条消息
  python cli.py --slow -c "问题"   # 使用慢思考模式
  python cli.py --list-nng         # 列出NNG节点
  python cli.py --list-memories    # 列出记忆
        """
    )
    
    parser.add_argument('-c', '--chat', type=str, help='发送单条消息')
    parser.add_argument('--slow', action='store_true', help='使用慢思考模式')
    parser.add_argument('--list-nng', action='store_true', help='列出NNG节点')
    parser.add_argument('--list-memories', action='store_true', help='列出记忆')
    parser.add_argument('--create-nng', nargs=3, metavar=('NODE_ID', 'CONTENT', 'PARENT_ID'),
                       help='创建NNG节点 (parent_id可为none)')
    parser.add_argument('--export-memory', nargs=2, metavar=('MEMORY_ID', 'FILEPATH'),
                       help='导出记忆到文件')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    parser.add_argument('--dmn', action='store_true', help='运行DMN维护')
    
    args = parser.parse_args()
    
    cli = AbyssACCLI()
    
    if args.chat:
        cli.chat(args.chat, slow=args.slow)
    elif args.list_nng:
        cli.list_nng()
    elif args.list_memories:
        cli.list_memories()
    elif args.create_nng:
        node_id, content, parent_id = args.create_nng
        parent_id = None if parent_id.lower() == 'none' else parent_id
        cli.create_nng(node_id, content, parent_id)
    elif args.export_memory:
        memory_id, filepath = args.export_memory
        cli.export_memory(memory_id, filepath)
    elif args.status:
        cli.show_status()
    elif args.dmn:
        cli.run_dmn()
    else:
        cli.interactive_mode()


if __name__ == "__main__":
    main()
