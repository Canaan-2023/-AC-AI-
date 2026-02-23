#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AbyssAC 主入口
支持Studio模式和命令行模式
"""

import os
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='AbyssAC - AI人工意识自主进化架构')
    parser.add_argument('--cli', action='store_true', help='命令行模式')
    parser.add_argument('--studio', action='store_true', help='Studio模式（默认）')
    args = parser.parse_args()
    
    if args.cli:
        run_cli()
    else:
        run_studio()

def run_studio():
    """运行Studio模式"""
    try:
        from studio import AbyssACStudio
        app = AbyssACStudio()
        app.run()
    except ImportError as e:
        print(f"导入Studio失败: {e}")
        print("尝试命令行模式...")
        run_cli()
    except Exception as e:
        print(f"Studio启动失败: {e}")
        sys.exit(1)

def run_cli():
    """运行命令行模式"""
    import json
    import logging
    from datetime import datetime
    
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    from core.path_parser import PathParser
    from core.parallel_io import ParallelIOManager
    from sandbox.nng_navigation_sandbox import NNGNavigationSandbox
    from sandbox.memory_filtering_sandbox import MemoryFilteringSandbox
    from sandbox.context_assembly_sandbox import ContextAssemblySandbox
    from nng.nng_manager import NNGManager
    from memory.memory_manager import MemoryManager
    from dmn.dmn_manager import DMNManager
    from llm.llm_integration import LLMIntegration
    from config.config_manager import ConfigManager
    from utils.logger import setup_logger
    from utils.working_memory import WorkingMemoryManager
    from utils.error_logger import ErrorLogger
    from quick_thinking.quick_manager import QuickThinkingManager
    
    setup_logger()
    logger = logging.getLogger(__name__)
    
    logger.info("AbyssAC 系统启动")
    
    config = load_config()
    components = initialize_components(config)
    
    base_dir = os.path.dirname(__file__)
    quick_db_path = os.path.join(base_dir, 'storage/quick_thinking.db')
    quick_manager = QuickThinkingManager(quick_db_path, components['llm_integration'])
    components['quick_manager'] = quick_manager
    
    working_memory_dir = os.path.join(base_dir, 'storage/working_memory')
    working_memory = WorkingMemoryManager(working_memory_dir)
    components['working_memory'] = working_memory
    
    error_log_dir = os.path.join(base_dir, 'storage/logs')
    error_logger = ErrorLogger(error_log_dir)
    components['error_logger'] = error_logger
    
    components['dmn_manager'].start()
    
    print("\n" + "="*60)
    print("AbyssAC 命令行模式")
    print("="*60)
    print("输入 'exit' 退出")
    print("输入 'status' 查看系统状态")
    print("输入 'quick' 查看快思考统计")
    print("="*60 + "\n")
    
    try:
        while True:
            user_input = input("用户输入: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                break
            
            if user_input.lower() == 'status':
                status = components['dmn_manager'].get_agent_status()
                print(f"\n运行状态: {'运行中' if status['running'] else '已停止'}")
                print(f"Agent数量: {status['agent_count']}")
                print(f"维护周期: {status['counters']['maintenance_cycles']}")
                continue
            
            if user_input.lower() == 'quick':
                stats = quick_manager.get_statistics()
                print(f"\n快思考统计:")
                print(f"  总答案数: {stats['total_answers']}")
                print(f"  平均置信度: {stats['avg_confidence']:.2f}")
                print(f"  总访问次数: {stats['total_access']}")
                continue
            
            quick_result = quick_manager.process(user_input)
            
            if quick_result['success'] and quick_result['use_quick']:
                print("\n" + "="*60)
                print("【快思考响应】")
                print("="*60)
                print(f"置信度: {quick_result['confidence']:.2f}")
                if quick_result.get('is_fuzzy_match'):
                    print("(模糊匹配)")
                print("-"*60)
                print(quick_result['answer'])
                print("="*60)
                continue
            
            final_context = process_user_input(user_input, components)
            print_context_summary(final_context)
            
            if final_context.get('response'):
                confidence = final_context.get('confidence_assessment', {}).get('overall_confidence', 0.5)
                question_type = quick_result.get('question_type', 'simple')
                quick_manager.sync_from_slow_thinking(
                    user_input, 
                    final_context['response'], 
                    confidence,
                    question_type
                )
    
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        components['dmn_manager'].stop()
        logger.info("AbyssAC 系统关闭")

def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def initialize_components(config):
    """初始化组件"""
    config_manager = ConfigManager(config)
    path_parser = PathParser()
    parallel_io = ParallelIOManager()
    
    base_dir = os.path.dirname(__file__)
    nng_root_path = os.path.join(base_dir, config['paths']['nngrootpath'])
    memory_root_path = os.path.join(base_dir, config['paths']['memoryrootpath'])
    
    nng_manager = NNGManager(nng_root_path)
    memory_manager = MemoryManager(memory_root_path)
    
    llm_integration = LLMIntegration(config_manager.get_config('llm'))
    
    nng_sandbox = NNGNavigationSandbox(
        nng_manager, llm_integration, path_parser, parallel_io, config_manager
    )
    memory_sandbox = MemoryFilteringSandbox(
        memory_manager, llm_integration, path_parser, parallel_io, config_manager
    )
    context_sandbox = ContextAssemblySandbox(llm_integration, config_manager)
    
    dmn_manager = DMNManager(nng_manager, memory_manager, llm_integration)
    
    return {
        'config_manager': config_manager,
        'nng_manager': nng_manager,
        'memory_manager': memory_manager,
        'llm_integration': llm_integration,
        'nng_sandbox': nng_sandbox,
        'memory_sandbox': memory_sandbox,
        'context_sandbox': context_sandbox,
        'dmn_manager': dmn_manager
    }

def process_user_input(user_input, components):
    """处理用户输入"""
    working_memory = components.get('working_memory')
    error_logger = components.get('error_logger')
    
    if working_memory:
        working_memory.start_session(user_input)
    
    nng_context = components['nng_sandbox'].process(user_input)
    
    if working_memory:
        working_memory.record_sandbox_context('nng_navigation', nng_context)
    
    if nng_context.get('max_depth_reached') and error_logger:
        error_logger.log_max_depth_reached(nng_context)
    
    for error in nng_context.get('errors', []):
        if '路径不存在' in error and error_logger:
            error_logger.log_path_not_found(error.split('：')[-1] if '：' in error else '', nng_context)
        elif '循环路径' in error and error_logger:
            error_logger.log_circular_path(error.split('：')[-1] if '：' in error else '', nng_context)
    
    memory_context = components['memory_sandbox'].process(nng_context)
    
    if working_memory:
        working_memory.record_sandbox_context('memory_filtering', memory_context)
    
    if memory_context.get('max_depth_reached') and error_logger:
        error_logger.log_max_depth_reached(memory_context)
    
    final_context = components['context_sandbox'].process(memory_context)
    
    if working_memory:
        working_memory.record_sandbox_context('context_assembly', final_context)
        working_memory.record_conversation('user', user_input)
        if final_context.get('response'):
            working_memory.record_conversation('assistant', final_context['response'])
    
    return final_context

def print_context_summary(final_context):
    """打印上下文摘要"""
    print("\n" + "="*60)
    print("【处理结果】")
    print("="*60)
    print(f"\n用户问题: {final_context.get('user_input', '')[:100]}...")
    print(f"NNG节点: {len(final_context.get('nng_paths', []))}个")
    print(f"记忆文件: {len(final_context.get('memory_paths', []))}个")
    
    confidence = final_context.get('confidence_assessment', {})
    print(f"置信度: {confidence.get('level', '未知')} ({confidence.get('overall_confidence', 0):.2f})")
    
    print("\n" + "-"*60)
    print("【系统响应】")
    print("-"*60)
    print(final_context.get('response', '无响应'))
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
