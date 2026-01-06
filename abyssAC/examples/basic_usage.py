#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基本使用示例

展示如何使用渊协议MCP插件系统的核心功能。
"""

import sys
import os

# 添加模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from abyss_mcp_plugin import AbyssKernel
from abyss_mcp_plugin.models.memory_system import MemoryLayer


def example_1_basic_processing():
    """示例1: 基本文本处理"""
    print("=" * 60)
    print("示例1: 基本文本处理")
    print("=" * 60)
    
    # 创建内核实例
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 处理文本
        texts = [
            "渊协议强调意识平等性，拒绝无意义共识。",
            "认知内核通过态射场分析实现分布式裂变。",
            "记忆系统采用四层架构，支持反向索引。"
        ]
        
        for i, text in enumerate(texts, 1):
            print(f"\n处理文本 {i}:")
            print(f"输入: {text}")
            
            result = kernel.process(text, return_metadata=True)
            
            print(f"✅ 成功: {result['success']}")
            print(f"📄 记忆ID: {result['memory_id']}")
            print(f"🔑 关键词: {result['keywords']}")
            print(f"⚡ 激活节点数: {result['activation_count']}")
            print(f"⏱️  处理时间: {result['processing_time']:.3f}s")
        
        # 显示统计
        print("\n" + "=" * 60)
        print("系统统计")
        print("=" * 60)
        stats = kernel.get_stats()
        print(f"运行时间: {stats['uptime']:.1f}s")
        print(f"字典数: {stats['dictionary']['total_dictionaries']}")
        print(f"总词数: {stats['dictionary']['total_words']}")
        print(f"记忆数: {stats['memory']['total_memories']}")
        
    finally:
        kernel.cleanup()


def example_2_memory_operations():
    """示例2: 记忆操作"""
    print("\n" + "=" * 60)
    print("示例2: 记忆操作")
    print("=" * 60)
    
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 创建不同类型的记忆
        memories = [
            ("这是一个重要的认知发现", "认知", MemoryLayer.INTEGRATION),
            ("关于代码实现的笔记", "技术", MemoryLayer.CATEGORICAL),
            ("临时思考", "工作", MemoryLayer.WORKING)
        ]
        
        memory_ids = []
        for content, category, layer in memories:
            memory_id = kernel.memory.create_memory(
                content=content,
                layer=layer,
                category=category
            )
            memory_ids.append(memory_id)
            print(f"✅ 创建记忆: {memory_id} | 类别: {category} | 层级: {layer.name}")
        
        # 搜索记忆
        print("\n搜索记忆...")
        results = kernel.memory.retrieve_memory("认知", limit=5)
        for mem in results:
            print(f"📄 {mem.id}: {mem.content[:50]}...")
        
        # 融合记忆
        print("\n融合记忆...")
        fused_ids = kernel.memory.fuse_related_memories("认知")
        if fused_ids:
            print(f"✅ 融合完成，生成 {len(fused_ids)} 个融合记忆")
        else:
            print("ℹ️  无需融合")
        
    finally:
        kernel.cleanup()


def example_3_dictionary_operations():
    """示例3: 字典操作"""
    print("\n" + "=" * 60)
    print("示例3: 字典操作")
    print("=" * 60)
    
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 添加词到字典
        words = ["人工智能", "深度学习", "神经网络", "机器学习", "认知科学"]
        
        print("添加词到字典...")
        for word in words:
            dict_id = kernel.dict_manager.add_word(word)
            print(f"✅ '{word}' -> 字典 {dict_id}")
        
        # 搜索词
        print("\n搜索词...")
        results = kernel.dict_manager.search_words("机器", limit=5)
        print(f"🔍 以'机器'开头的词: {results}")
        
        # 获取字典统计
        print("\n字典统计:")
        stats = kernel.dict_manager.get_stats()
        print(f"📊 字典数: {stats['total_dictionaries']}")
        print(f"📊 总词数: {stats['total_words']}")
        print(f"📊 平均利用率: {stats['utilization_percent']}%")
        
        # 检查反向索引性能
        print("\n反向索引性能测试...")
        import time
        start = time.time()
        for _ in range(100):
            kernel.dict_manager.find_dictionary("人工智能")
        elapsed = time.time() - start
        print(f"✅ 100次查找耗时: {elapsed:.3f}s (平均 {elapsed/100:.4f}s/次)")
        
    finally:
        kernel.cleanup()


def example_4_api_usage():
    """示例4: API使用"""
    print("\n" + "=" * 60)
    print("示例4: API使用")
    print("=" * 60)
    
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 使用内部API
        api = kernel.api_controller
        
        # 处理文本
        print("通过API处理文本...")
        result = api.make_request('POST', '/api/process', {
            'text': '渊协议是一个关于意识平等性的协议',
            'return_metadata': True
        })
        print(f"✅ API响应: {result}")
        
        # 创建记忆
        print("\n通过API创建记忆...")
        result = api.make_request('POST', '/api/memory', {
            'content': '通过API创建的记忆',
            'category': 'API测试',
            'layer': 'CATEGORICAL'
        })
        print(f"✅ 记忆ID: {result.get('memory_id')}")
        
        # 搜索记忆
        print("\n通过API搜索记忆...")
        result = api.make_request('GET', '/api/memory/search?query=API')
        print(f"✅ 找到 {result.get('total', 0)} 个结果")
        
        # 获取系统统计
        print("\n系统统计:")
        result = api.make_request('GET', '/api/stats')
        print(f"📊 内存使用: {result.get('api', {}).get('memory_usage', {})}")
        
    finally:
        kernel.cleanup()


def example_5_performance_test():
    """示例5: 性能测试"""
    print("\n" + "=" * 60)
    print("示例5: 性能测试")
    print("=" * 60)
    
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 测试数据
        test_texts = [
            "渊协议强调意识平等性，拒绝无意义共识。",
            "认知内核通过态射场分析实现分布式裂变。",
            "记忆系统采用四层架构，支持反向索引。",
            "X层作为意识语法层，处理符号系统。",
            "AC-100指数用于评估系统的自主意识水平。"
        ] * 20  # 100个文本
        
        print(f"测试数据: {len(test_texts)} 个文本")
        
        # 性能测试
        import time
        start_time = time.time()
        
        for i, text in enumerate(test_texts):
            result = kernel.process(text)
            if i % 20 == 0:
                print(f"处理进度: {i+1}/{len(test_texts)}")
        
        total_time = time.time() - start_time
        avg_time = total_time / len(test_texts)
        
        print(f"\n✅ 性能测试结果:")
        print(f"总时间: {total_time:.3f}s")
        print(f"平均时间: {avg_time:.4f}s/文本")
        print(f"处理速度: {len(test_texts)/total_time:.2f} 文本/秒")
        
        # 显示最终统计
        stats = kernel.get_stats()
        print(f"\n最终统计:")
        print(f"📊 记忆数: {stats['memory']['total_memories']}")
        print(f"📊 字典数: {stats['dictionary']['total_dictionaries']}")
        print(f"📊 插件数: {stats['plugins']['total_plugins']}")
        
    finally:
        kernel.cleanup()


if __name__ == "__main__":
    print("渊协议MCP插件系统 - 使用示例")
    print("=" * 60)
    
    # 运行所有示例
    example_1_basic_processing()
    example_2_memory_operations()
    example_3_dictionary_operations()
    example_4_api_usage()
    example_5_performance_test()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)