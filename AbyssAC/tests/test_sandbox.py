"""三层沙盒测试"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.sandbox import ThreeLayerSandbox, NavigationResult, MemoryFilterResult


class MockLLMInterface:
    """模拟LLM接口"""
    
    def __init__(self):
        self.responses = []
        self.call_count = 0
    
    def chat(self, messages, **kwargs):
        """模拟聊天响应"""
        self.call_count += 1
        if self.responses:
            response = self.responses.pop(0)
            return Mock(
                success=True,
                content=response,
                error=None
            )
        
        # 默认响应
        return Mock(
            success=True,
            content="STAY",
            error=None
        )
    
    def validate_navigation_response(self, content):
        """验证导航响应"""
        valid_commands = ['GOTO', 'STAY', 'BACK', 'ROOT', 'NNG']
        return any(cmd in content for cmd in valid_commands)


class TestThreeLayerSandbox(unittest.TestCase):
    """测试三层沙盒"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        
        # 创建模拟对象
        from core.memory_manager import MemoryManager
        from core.nng_navigator import NNGNavigator
        
        self.mm = MemoryManager(base_path=self.test_dir)
        self.nav = NNGNavigator(base_path=os.path.join(self.test_dir, "nng"))
        self.llm = MockLLMInterface()
        
        self.sandbox = ThreeLayerSandbox(
            memory_manager=self.mm,
            nng_navigator=self.nav,
            llm_interface=self.llm,
            max_depth=5
        )
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_navigation_stay(self):
        """测试STAY导航"""
        self.llm.responses = ["STAY"]
        
        result = self.sandbox._single_navigation("测试输入", [])
        
        self.assertTrue(result.success)
        self.assertEqual(result.selected_nodes, [])
    
    def test_navigation_goto(self):
        """测试GOTO导航"""
        # 创建节点
        self.nav.create_node("1", "技术", 80)
        self.nav.create_node("1.1", "Python", 75)
        
        self.llm.responses = ["GOTO(1)", "GOTO(1.1)", "STAY"]
        
        result = self.sandbox._single_navigation("Python是什么", [])
        
        self.assertTrue(result.success)
        self.assertIn("1.1", result.selected_nodes)
    
    def test_navigation_back(self):
        """测试BACK导航"""
        self.nav.create_node("1", "技术", 80)
        self.nav.create_node("1.1", "Python", 75)
        
        self.llm.responses = ["GOTO(1)", "GOTO(1.1)", "BACK", "STAY"]
        
        result = self.sandbox._single_navigation("测试", [])
        
        self.assertTrue(result.success)
    
    def test_navigation_max_depth(self):
        """测试最大深度限制"""
        self.nav.create_node("1", "节点1", 80)
        self.nav.create_node("1.1", "节点1.1", 75)
        self.nav.create_node("1.1.1", "节点1.1.1", 70)
        
        # 模拟一直GOTO
        self.llm.responses = ["GOTO(1)", "GOTO(1.1)", "GOTO(1.1.1)"]
        
        # 设置较小的max_depth
        self.sandbox.max_depth = 2
        
        result = self.sandbox._single_navigation("测试", [])
        
        self.assertFalse(result.success)
        self.assertIn("最大导航深度", result.error)
    
    def test_memory_filter_no_memories(self):
        """测试无记忆时的筛选"""
        result = self.sandbox.layer2_memory_filter("测试", ["1"])
        
        self.assertTrue(result.success)
        self.assertEqual(result.selected_memory_ids, [])
    
    def test_memory_filter_with_memories(self):
        """测试有记忆时的筛选"""
        from core.memory_manager import MemoryType
        
        # 创建记忆
        mem_id = self.mm.create_memory(
            memory_type=MemoryType.CLASSIFIED,
            user_input="Python是什么",
            ai_response="Python是一种编程语言",
            confidence=80
        )
        
        # 创建节点并关联记忆
        self.nav.create_node("1", "技术", 80)
        self.nav.add_memory_summary("1", mem_id, "Python介绍", "分类记忆", "高")
        self.mm.add_nng_association(mem_id, "1")
        
        self.llm.responses = [f"记忆{mem_id},STAY"]
        
        result = self.sandbox.layer2_memory_filter("Python", ["1"])
        
        self.assertTrue(result.success)
        self.assertIn(mem_id, result.selected_memory_ids)
    
    def test_context_assembly(self):
        """测试上下文组装"""
        memories = ["记忆1内容", "记忆2内容"]
        
        self.llm.responses = ["整合后的上下文"]
        
        result = self.sandbox.layer3_context_assembly("问题", memories)
        
        self.assertTrue(result.success)
        self.assertEqual(result.assembled_context, "整合后的上下文")
    
    def test_full_sandbox_no_memory_needed(self):
        """测试不需要记忆的完整流程"""
        # 模拟不需要记忆的判断
        def mock_needs_memory(user_input):
            return False
        
        # 这里需要修改主程序逻辑，暂时跳过
        pass
    
    def test_navigation_stats(self):
        """测试导航统计"""
        stats = self.sandbox.get_navigation_stats()
        
        self.assertIn("total_logs", stats)
        self.assertIn("failure_count", stats)


if __name__ == "__main__":
    unittest.main()
