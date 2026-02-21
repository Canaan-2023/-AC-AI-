"""
AbyssAC System Test
系统测试脚本 - 验证核心功能
"""

import os
import sys
import json

def test_imports():
    """测试模块导入"""
    print("[测试] 模块导入...")
    try:
        from config.system_config import get_config
        from core.nng_manager import get_nng_manager
        from core.memory_manager import get_memory_manager
        from core.llm_interface import get_llm_interface
        from core.sandbox import get_sandbox
        from core.dmn_system import get_dmn_system
        from core.quick_thinking import get_quick_system
        from core.ai_dev_space import get_dev_space
        from core.main_system import get_system
        print("  ✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        return False


def test_config():
    """测试配置系统"""
    print("[测试] 配置系统...")
    try:
        from config.system_config import get_config
        config = get_config()
        
        # 检查路径配置
        assert config.paths.nng_root_path == "storage/nng/"
        assert config.paths.memory_root_path == "storage/Y层记忆库/"
        
        # 检查占位符替换
        values = config.get_placeholder_values()
        assert "{nng_root_path}" in values
        
        print("  ✓ 配置系统正常")
        return True
    except Exception as e:
        print(f"  ✗ 配置测试失败: {e}")
        return False


def test_nng_manager():
    """测试NNG管理器"""
    print("[测试] NNG管理器...")
    try:
        from core.nng_manager import get_nng_manager
        nng = get_nng_manager()
        
        # 检查root.json
        root_content = nng.get_root_content()
        root_data = json.loads(root_content)
        assert "一级节点" in root_data
        
        # 列出节点
        nodes = nng.list_all_nodes()
        print(f"  发现 {len(nodes)} 个NNG节点")
        
        # 读取示例节点
        if nodes:
            node = nng.read_node(nodes[0])
            if node:
                print(f"  节点 {nodes[0]}: {node.content[:30]}...")
        
        print("  ✓ NNG管理器正常")
        return True
    except Exception as e:
        print(f"  ✗ NNG测试失败: {e}")
        return False


def test_memory_manager():
    """测试记忆管理器"""
    print("[测试] 记忆管理器...")
    try:
        from core.memory_manager import get_memory_manager
        mm = get_memory_manager()
        
        # 列出记忆
        memories = mm.list_memories(limit=10)
        print(f"  发现 {len(memories)} 条记忆")
        
        # 读取示例记忆
        if memories:
            memory = mm.read_memory(memories[0]['memory_id'])
            if memory:
                print(f"  记忆 {memories[0]['memory_id']}: {memory.user_input[:30]}...")
        
        print("  ✓ 记忆管理器正常")
        return True
    except Exception as e:
        print(f"  ✗ 记忆测试失败: {e}")
        return False


def test_ai_dev_space():
    """测试AI开发空间"""
    print("[测试] AI开发空间...")
    try:
        from core.ai_dev_space import get_dev_space, get_sandbox
        dev = get_dev_space()
        sandbox = get_sandbox()
        
        # 列出文件
        files = dev.list_files()
        print(f"  发现 {len(files)} 个文件")
        
        # 测试沙箱执行
        result = sandbox.execute_code("print('Hello from sandbox')", language='python')
        if result.success:
            print(f"  沙箱执行成功: {result.stdout.strip()}")
        else:
            print(f"  沙箱执行结果: return_code={result.return_code}")
        
        print("  ✓ AI开发空间正常")
        return True
    except Exception as e:
        print(f"  ✗ AI开发空间测试失败: {e}")
        return False


def test_quick_thinking():
    """测试快思考系统"""
    print("[测试] 快思考系统...")
    try:
        from core.quick_thinking import get_quick_system
        qt = get_quick_system()
        
        # 列出答案
        answers = qt.db.list_all(limit=5)
        print(f"  数据库中有 {len(answers)} 条快答案")
        
        print("  ✓ 快思考系统正常")
        return True
    except Exception as e:
        print(f"  ✗ 快思考测试失败: {e}")
        return False


def test_main_system():
    """测试主系统"""
    print("[测试] 主系统...")
    try:
        from core.main_system import get_system
        system = get_system()
        
        # 检查系统状态
        status = system.get_system_status()
        print(f"  记忆计数器: {status['memory_counter']}")
        print(f"  NNG节点数: {status['nng_nodes']}")
        print(f"  工作记忆数: {status['work_memories']}")
        print(f"  LLM连接: {'已连接' if status['llm_connected'] else '未连接'}")
        
        print("  ✓ 主系统正常")
        return True
    except Exception as e:
        print(f"  ✗ 主系统测试失败: {e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("[测试] 目录结构...")
    required_dirs = [
        "storage/nng",
        "storage/Y层记忆库/元认知记忆",
        "storage/Y层记忆库/分类记忆/高价值",
        "storage/Y层记忆库/工作记忆",
        "storage/AI开发空间",
        "storage/沙箱",
        "temp",
        "logs",
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            missing.append(dir_path)
    
    if missing:
        print(f"  ✗ 缺少目录: {', '.join(missing)}")
        return False
    
    print(f"  ✓ 所有必要目录存在 ({len(required_dirs)}个)")
    return True


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("  AbyssAC 系统测试")
    print("="*60)
    print()
    
    tests = [
        ("目录结构", test_directory_structure),
        ("模块导入", test_imports),
        ("配置系统", test_config),
        ("NNG管理器", test_nng_manager),
        ("记忆管理器", test_memory_manager),
        ("AI开发空间", test_ai_dev_space),
        ("快思考系统", test_quick_thinking),
        ("主系统", test_main_system),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ✗ {name}测试异常: {e}")
            failed += 1
        print()
    
    print("="*60)
    print(f"  测试结果: {passed} 通过, {failed} 失败")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
