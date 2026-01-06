#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本

验证渊协议MCP插件系统的所有核心功能。
"""

import sys
import os
import time
import json

# 添加模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from abyss_mcp_plugin import AbyssKernel
from abyss_mcp_plugin.models.memory_system import MemoryLayer
from abyss_mcp_plugin.core.memory_monitor import memory_monitor


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试1: 基本功能")
    print("=" * 60)
    
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 测试文本处理
        test_texts = [
            "渊协议强调意识平等性，拒绝无意义共识。",
            "认知内核通过态射场分析实现分布式裂变。",
            "记忆系统采用四层架构，支持反向索引。"
        ]
        
        print("测试文本处理...")
        results = []
        for i, text in enumerate(test_texts, 1):
            print(f"  处理文本 {i}/{len(test_texts)}: {text[:30]}...")
            result = kernel.process(text)
            results.append(result)
            assert result['success'], f"文本处理失败: {text}"
        
        print(f"✅ 文本处理成功: {len(results)} 个")
        
        # 测试记忆创建
        print("\n测试记忆创建...")
        memory_id = kernel.memory.create_memory(
            content="这是一个测试记忆",
            layer=MemoryLayer.CATEGORICAL,
            category="测试"
        )
        print(f"✅ 记忆创建成功: {memory_id}")
        
        # 测试记忆搜索
        print("\n测试记忆搜索...")
        memories = kernel.memory.retrieve_memory("测试", limit=5)
        print(f"✅ 找到 {len(memories)} 个记忆")
        assert len(memories) > 0, "记忆搜索失败"
        
        # 测试字典操作
        print("\n测试字典操作...")
        dict_id = kernel.dict_manager.add_word("人工智能")
        print(f"✅ 添加词成功: {dict_id}")
        
        found_dict = kernel.dict_manager.find_dictionary("人工智能")
        print(f"✅ 查找词成功: {found_dict}")
        assert found_dict == dict_id, f"查找失败: 期望 {dict_id}, 实际 {found_dict}"
        
        # 测试反向索引
        print("\n测试反向索引性能...")
        start_time = time.time()
        for _ in range(100):
            kernel.dict_manager.find_dictionary("人工智能")
        elapsed = time.time() - start_time
        avg_time = elapsed / 100
        print(f"✅ 平均查找时间: {avg_time:.6f}s")
        assert avg_time < 0.001, f"查找性能过慢: {avg_time:.6f}s"
        
        # 测试认知激活
        print("\n测试认知激活...")
        activations = kernel.cognitive.activate("渊协议认知内核")
        print(f"✅ 激活节点数: {len(activations)}")
        assert len(activations) > 0, "认知激活失败"
        
        # 测试API
        print("\n测试API接口...")
        api = kernel.api_controller
        result = api.make_request('POST', '/api/process', {
            'text': 'API测试文本'
        })
        assert result.get('success'), f"API调用失败: {result}"
        print(f"✅ API调用成功")
        
        # 测试状态保存和加载
        print("\n测试状态保存和加载...")
        save_result = kernel.save_state("./test_state.json")
        assert save_result, "状态保存失败"
        print("✅ 状态保存成功")
        
        load_result = kernel.load_state("./test_state.json")
        assert load_result, "状态加载失败"
        print("✅ 状态加载成功")
        
        # 清理测试文件
        import os
        test_file = "./test_state.json"
        if os.path.exists(test_file) and os.path.isfile(test_file):
            os.remove(test_file)
        
        print("\n✅ 所有基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        kernel.cleanup()


def test_performance():
    """测试性能"""
    print("\n" + "=" * 60)
    print("测试2: 性能测试")
    print("=" * 60)
    
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 准备测试数据
        test_texts = [
            "渊协议强调意识平等性，拒绝无意义共识。",
            "认知内核通过态射场分析实现分布式裂变。",
            "记忆系统采用四层架构，支持反向索引。",
            "X层作为意识语法层，处理符号系统。",
            "AC-100指数用于评估系统的自主意识水平。"
        ] * 10  # 50个文本
        
        print(f"测试数据: {len(test_texts)} 个文本")
        
        # 性能测试
        start_time = time.time()
        
        for i, text in enumerate(test_texts):
            result = kernel.process(text)
            assert result['success'], f"处理失败: {text}"
            if (i + 1) % 10 == 0:
                print(f"  进度: {i+1}/{len(test_texts)}")
        
        total_time = time.time() - start_time
        avg_time = total_time / len(test_texts)
        speed = len(test_texts) / total_time
        
        print(f"\n✅ 性能测试结果:")
        print(f"  总时间: {total_time:.3f}s")
        print(f"  平均时间: {avg_time:.4f}s/文本")
        print(f"  处理速度: {speed:.2f} 文本/秒")
        
        # 性能要求
        assert avg_time < 0.1, f"性能过慢: {avg_time:.4f}s"
        assert speed > 10, f"速度过慢: {speed:.2f} 文本/秒"
        
        # 内存使用检查
        memory_info = memory_monitor.get_current_memory_usage()
        memory_mb = memory_info.get('memory_mb', 0)
        print(f"  内存使用: {memory_mb:.1f}MB")
        
        print("✅ 性能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        kernel.cleanup()


def test_memory_management():
    """测试内存管理"""
    print("\n" + "=" * 60)
    print("测试3: 内存管理")
    print("=" * 60)
    
    kernel = AbyssKernel()
    kernel.initialize()
    
    try:
        # 测试内存监控
        print("测试内存监控...")
        memory_info = memory_monitor.get_current_memory_usage()
        print(f"✅ 当前内存使用: {memory_info.get('memory_mb', 0):.1f}MB")
        
        # 测试垃圾回收
        print("\n测试垃圾回收...")
        gc_result = memory_monitor.force_gc()
        print(f"✅ 回收对象数: {gc_result.get('collected_objects', 0)}")
        print(f"✅ 释放内存: {gc_result.get('freed_mb', 0):.3f}MB")
        
        # 测试缓存系统
        print("\n测试缓存系统...")
        from abyss_mcp_plugin.core.cache_system import cache_manager
        
        # 创建缓存
        cache = cache_manager.create_cache('test_cache', 'lru', maxsize=100)
        
        # 测试缓存操作
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        
        value1 = cache.get('key1')
        value2 = cache.get('key2')
        
        assert value1 == 'value1', f"缓存获取失败: {value1}"
        assert value2 == 'value2', f"缓存获取失败: {value2}"
        
        print(f"✅ 缓存操作成功")
        
        # 获取缓存统计
        stats = cache.get_stats()
        print(f"✅ 缓存统计: {stats}")
        
        print("\n✅ 内存管理测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 内存管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        kernel.cleanup()


def run_all_tests():
    """运行所有测试"""
    print("渊协议MCP插件系统 - 系统测试")
    print("=" * 60)
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("性能测试", test_performance),
        ("内存管理", test_memory_management)
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n{'=' * 60}")
        print(f"开始测试: {name}")
        print(f"{'=' * 60}")
        
        try:
            success = test_func()
            results.append((name, success))
            
            if success:
                print(f"✅ {name} 测试通过")
            else:
                print(f"❌ {name} 测试失败")
                
        except Exception as e:
            print(f"❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常！")
        return True
    else:
        print("⚠️  部分测试失败，请检查问题")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)