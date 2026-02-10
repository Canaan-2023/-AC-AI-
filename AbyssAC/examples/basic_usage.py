"""AbyssAC 基础使用示例

展示系统的基本使用方法。
"""

import os
import sys
import tempfile
import shutil

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory_manager import MemoryManager, MemoryType, ValueLevel
from core.nng_navigator import NNGNavigator


def example_1_basic_memory():
    """示例1: 基础记忆操作"""
    print("=" * 50)
    print("示例1: 基础记忆操作")
    print("=" * 50)
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp()
    
    try:
        # 初始化记忆管理器
        mm = MemoryManager(base_path=test_dir)
        
        # 创建分类记忆
        mem_id = mm.create_memory(
            memory_type=MemoryType.CLASSIFIED,
            user_input="什么是Python的GIL？",
            ai_response="GIL（全局解释器锁）是Python解释器中的一个机制...",
            confidence=85,
            value_level=ValueLevel.HIGH,
            associated_nngs=["1.2.3"]
        )
        print(f"创建记忆成功，ID: {mem_id}")
        
        # 读取记忆
        content = mm.get_memory(mem_id)
        print(f"记忆内容:\n{content[:200]}...")
        
        # 更新置信度
        mm.update_confidence(mem_id, -10)
        meta = mm.get_memory_metadata(mem_id)
        print(f"更新后置信度: {meta.confidence}")
        
        # 获取统计
        stats = mm.get_statistics()
        print(f"记忆统计: {stats}")
    
    finally:
        # 清理
        shutil.rmtree(test_dir, ignore_errors=True)
    
    print()


def example_2_nng_navigation():
    """示例2: NNG导航操作"""
    print("=" * 50)
    print("示例2: NNG导航操作")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp()
    
    try:
        # 初始化NNG导航器
        nav = NNGNavigator(base_path=test_dir)
        
        # 创建节点结构
        nav.create_node("1", "技术知识", 90)
        nav.create_node("1.1", "编程语言", 85)
        nav.create_node("1.1.1", "Python", 80)
        nav.create_node("1.1.2", "JavaScript", 75)
        nav.create_node("1.2", "数据库", 80)
        
        print("创建的NNG结构:")
        
        # 获取根节点
        root = nav.get_root()
        print(f"根节点: {root}")
        
        # 获取子节点
        children = nav.get_children("1")
        print(f"节点1的子节点: {children}")
        
        # 导航测试
        current = "1"
        print(f"\n导航测试:")
        print(f"当前位置: {current}")
        
        new_loc, success = nav.navigate(current, "GOTO", "1.1")
        print(f"GOTO(1.1): {new_loc}, 成功: {success}")
        
        new_loc, success = nav.navigate(new_loc, "BACK")
        print(f"BACK: {new_loc}")
        
        # 验证完整性
        integrity = nav.verify_integrity()
        print(f"\nNNG完整性: {integrity['valid']}")
        print(f"总节点数: {integrity['stats']['total_nodes']}")
    
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
    
    print()


def example_3_memory_nng_association():
    """示例3: 记忆与NNG关联"""
    print("=" * 50)
    print("示例3: 记忆与NNG关联")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp()
    
    try:
        # 初始化
        mm = MemoryManager(base_path=test_dir)
        nav = NNGNavigator(base_path=os.path.join(test_dir, "nng"))
        
        # 创建NNG节点
        nav.create_node("1", "编程知识", 85)
        
        # 创建记忆并关联
        mem_id = mm.create_memory(
            memory_type=MemoryType.CLASSIFIED,
            user_input="Python的装饰器是什么？",
            ai_response="装饰器是Python中的一种语法糖...",
            confidence=80,
            value_level=ValueLevel.MEDIUM
        )
        
        # 双向关联
        mm.add_nng_association(mem_id, "1")
        nav.add_memory_summary("1", mem_id, "Python装饰器介绍", "分类记忆", "中")
        
        print(f"创建记忆 ID: {mem_id}")
        print(f"关联到 NNG: 1")
        
        # 通过NNG查找记忆
        memories = mm.get_memories_by_nng("1")
        print(f"NNG节点1关联的记忆: {memories}")
        
        # 通过记忆查找NNG
        meta = mm.get_memory_metadata(mem_id)
        print(f"记忆{mem_id}关联的NNG: {meta.associated_nngs}")
    
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
    
    print()


def example_4_working_memory():
    """示例4: 工作记忆生命周期"""
    print("=" * 50)
    print("示例4: 工作记忆生命周期")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp()
    
    try:
        mm = MemoryManager(base_path=test_dir)
        
        # 模拟对话，创建多条工作记忆
        conversations = [
            ("你好", "你好！有什么可以帮助你的？"),
            ("Python是什么", "Python是一种流行的编程语言..."),
            ("有什么特点", "Python的特点包括简洁、易读..."),
        ]
        
        for user_input, ai_response in conversations:
            mem_id = mm.create_memory(
                memory_type=MemoryType.WORKING,
                user_input=user_input,
                ai_response=ai_response,
                confidence=70
            )
            print(f"创建工作记忆: ID={mem_id}")
        
        # 查看工作记忆数量
        count = mm.get_working_memory_count()
        print(f"\n工作记忆总数: {count}")
        
        # 获取工作记忆
        memories = mm.get_working_memories()
        print(f"工作记忆列表:")
        for mem_id, content in memories:
            print(f"  ID {mem_id}: {content[:50]}...")
        
        # 模拟DMN清理
        print(f"\n清空工作记忆...")
        cleared = mm.clear_working_memory()
        print(f"清除了 {cleared} 条工作记忆")
        
        count = mm.get_working_memory_count()
        print(f"剩余工作记忆: {count}")
    
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
    
    print()


def example_5_statistics():
    """示例5: 系统统计"""
    print("=" * 50)
    print("示例5: 系统统计")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp()
    
    try:
        mm = MemoryManager(base_path=test_dir)
        nav = NNGNavigator(base_path=os.path.join(test_dir, "nng"))
        
        # 创建一些数据
        mm.create_memory(MemoryType.META_COGNITIVE, "反思1", "内容1", 80)
        mm.create_memory(MemoryType.HIGH_LEVEL, "整合1", "内容1", 75)
        mm.create_memory(MemoryType.CLASSIFIED, "分类1", "内容1", 70, ValueLevel.HIGH)
        mm.create_memory(MemoryType.CLASSIFIED, "分类2", "内容2", 65, ValueLevel.MEDIUM)
        mm.create_memory(MemoryType.CLASSIFIED, "分类3", "内容3", 60, ValueLevel.LOW)
        
        nav.create_node("1", "节点1", 80)
        nav.create_node("1.1", "节点1.1", 75)
        nav.create_node("2", "节点2", 70)
        
        # 获取统计
        print("记忆统计:")
        mem_stats = mm.get_statistics()
        for key, value in mem_stats.items():
            print(f"  {key}: {value}")
        
        print("\nNNG统计:")
        nng_stats = nav.get_statistics()
        for key, value in nng_stats.items():
            print(f"  {key}: {value}")
    
    finally:
        shutil.rmtree(test_dir, ignore_errors=True)
    
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("AbyssAC 基础使用示例")
    print("=" * 50 + "\n")
    
    example_1_basic_memory()
    example_2_nng_navigation()
    example_3_memory_nng_association()
    example_4_working_memory()
    example_5_statistics()
    
    print("=" * 50)
    print("所有示例执行完成")
    print("=" * 50)
